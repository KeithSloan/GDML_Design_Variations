#include "Recorder.hh"

#include <chrono>
#include <iomanip>
#include <sstream>

#include "CountingExceptionHandler.hh"
#include "EdepSD.hh"

#include "G4LogicalVolume.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4Material.hh"
#include "G4PhysicalVolumeStore.hh"
#include "G4Run.hh"
#include "G4SystemOfUnits.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VSensitiveDetector.hh"
#include "G4Version.hh"

namespace
{
double Now()
{
  using namespace std::chrono;
  return duration<double>(steady_clock::now().time_since_epoch()).count();
}

std::string Quote(const std::string& s)
{
  std::string out = "\"";
  for (char c : s) {
    if (c == '"' || c == '\\') {
      out += '\\';
      out += c;
    }
    else if (c == '\n') {
      out += "\\n";
    }
    else if (static_cast<unsigned char>(c) >= 0x20) {
      out += c;
    }
  }
  return out + "\"";
}

// Number of physical volumes placing lv (the world counts as one).
G4long Placements(const G4LogicalVolume* lv)
{
  G4long n = 0;
  for (const G4VPhysicalVolume* pv : *G4PhysicalVolumeStore::GetInstance()) {
    if (pv->GetLogicalVolume() == lv) {
      n += pv->GetMultiplicity();
    }
  }
  return n;
}
}  // namespace

Recorder& Recorder::Instance()
{
  static Recorder instance;
  return instance;
}

G4String Recorder::Path(const G4String& name) const
{
  return fOutDir + "/" + name;
}

void Recorder::AddDetector(EdepSD* sd)
{
  const G4String name = sd->GetName();
  if (fDets.find(name) == fDets.end()) {
    fOrder.push_back(name);
  }
  fDets[name].sd = sd;
}

void Recorder::AddDetectorVolume(const G4String& sdName, G4LogicalVolume* lv)
{
  fDets[sdName].volumes.push_back(lv);
}

void Recorder::BeginRun()
{
  for (auto& entry : fDets) {
    DetSums& d = entry.second;
    d.sum = d.sum2 = 0.;
    d.nonZero = d.uncollided = 0;
    d.copies.clear();
  }
  fNEvents = 0;
  fStartTime = Now();

  fEvents.open(Path("events.csv"));
  fEvents << "event";
  for (const auto& name : fOrder) {
    fEvents << ',' << name << "_edep_MeV";
  }
  for (const auto& name : fOrder) {
    fEvents << ',' << name << "_uncollided";
  }
  fEvents << '\n' << std::setprecision(9);
}

void Recorder::EndEvent(G4int eventID)
{
  fEvents << eventID;
  for (const auto& name : fOrder) {
    DetSums& d = fDets[name];
    G4double total = 0.;
    for (const auto& [copy, e] : d.sd->EventEdep()) {
      total += e;
      CopySums& c = d.copies[copy];
      c.sum += e;
      c.sum2 += e * e;
    }
    if (total > 0.) {
      ++d.nonZero;
    }
    d.sum += total;
    d.sum2 += total * total;
    fEvents << ',' << total / MeV;
  }
  for (const auto& name : fOrder) {
    DetSums& d = fDets[name];
    const G4bool u = d.sd->EventUncollided();
    if (u) {
      ++d.uncollided;
    }
    fEvents << ',' << (u ? 1 : 0);
  }
  fEvents << '\n';
  ++fNEvents;
}

void Recorder::EndRun(const G4Run* run)
{
  fEvents.close();
  WriteSummary(run, Now() - fStartTime);
}

void Recorder::WriteSummary(const G4Run* run, G4double seconds) const
{
  std::ofstream out(Path("summary.json"));
  out << std::setprecision(10);
  out << "{\n";
  out << "  \"app\": \"gdmlvar\",\n";
  out << "  \"geant4_version\": " << Quote(G4Version) << ",\n";
  for (const auto& [key, value] : fInfo) {
    out << "  " << Quote(key) << ": " << Quote(value) << ",\n";
  }
  out << "  \"events\": " << run->GetNumberOfEvent() << ",\n";
  out << "  \"wall_seconds\": " << seconds << ",\n";

  out << "  \"exceptions\": {";
  if (fHandler != nullptr) {
    G4bool first = true;
    for (const auto& [code, n] : fHandler->Counts()) {
      out << (first ? "" : ", ") << Quote(code) << ": " << n;
      first = false;
    }
  }
  out << "},\n";

  out << "  \"detectors\": {\n";
  for (std::size_t i = 0; i < fOrder.size(); ++i) {
    const DetSums& d = fDets.at(fOrder[i]);
    G4double mass = 0.;
    out << "    " << Quote(fOrder[i]) << ": {\n";
    out << "      \"volumes\": [";
    for (std::size_t j = 0; j < d.volumes.size(); ++j) {
      out << (j ? ", " : "") << Quote(d.volumes[j]->GetName());
    }
    out << "],\n";
    // Total mass = mass of each logical volume x its placements in its
    // mother (volumes placed inside repeated mothers are not multiplied).
    G4long placements = 0;
    for (auto* lv : d.volumes) {
      const G4long n = Placements(lv);
      placements += n;
      mass += n * lv->GetMass(true, false) / kg;
    }
    out << "      \"placements\": " << placements << ",\n";
    out << "      \"mass_kg\": " << mass << ",\n";
    out << "      \"sum_edep_MeV\": " << d.sum / MeV << ",\n";
    out << "      \"sum2_edep_MeV2\": " << d.sum2 / (MeV * MeV) << ",\n";
    out << "      \"events_with_edep\": " << d.nonZero << ",\n";
    out << "      \"uncollided\": " << d.uncollided << ",\n";
    out << "      \"copies\": {";
    G4bool first = true;
    for (const auto& [copy, c] : d.copies) {
      out << (first ? "" : ", ") << "\"" << copy << "\": [" << c.sum / MeV << ", "
          << c.sum2 / (MeV * MeV) << "]";
      first = false;
    }
    out << "}\n";
    out << "    }" << (i + 1 < fOrder.size() ? "," : "") << "\n";
  }
  out << "  },\n";

  out << "  \"volumes\": [\n";
  const G4LogicalVolumeStore* store = G4LogicalVolumeStore::GetInstance();
  for (std::size_t i = 0; i < store->size(); ++i) {
    G4LogicalVolume* lv = (*store)[i];
    const G4Material* mat = lv->GetMaterial();
    const G4VSensitiveDetector* sd = lv->GetSensitiveDetector();
    out << "    {\"name\": " << Quote(lv->GetName())
        << ", \"material\": " << Quote(mat != nullptr ? mat->GetName() : "")
        << ", \"density_g_cm3\": " << (mat != nullptr ? mat->GetDensity() / (g / cm3) : 0.)
        << ", \"radlen_mm\": " << (mat != nullptr ? mat->GetRadlen() / mm : 0.)
        << ", \"nuclear_int_length_mm\": "
        << (mat != nullptr ? mat->GetNuclearInterLength() / mm : 0.)
        << ", \"mass_kg\": " << lv->GetMass(true, false) / kg
        << ", \"placements\": " << Placements(lv)
        << ", \"daughters\": " << lv->GetNoDaughters()
        << ", \"sensdet\": " << Quote(sd != nullptr ? sd->GetName() : "") << "}"
        << (i + 1 < store->size() ? ",\n" : "\n");
  }
  out << "  ]\n";
  out << "}\n";
}
