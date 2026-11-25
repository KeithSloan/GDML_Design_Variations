#include "DetectorConstruction.hh"

#include "EdepSD.hh"
#include "Recorder.hh"

#include "G4LogicalVolume.hh"
#include "G4SDManager.hh"
#include "G4VPhysicalVolume.hh"

DetectorConstruction::DetectorConstruction(const G4String& gdmlFile, G4bool overlapCheck)
  : fFile(gdmlFile), fOverlapCheck(overlapCheck)
{}

G4VPhysicalVolume* DetectorConstruction::Construct()
{
  // Overlaps found while reading are reported as G4Exception GeomVol1002,
  // which the CountingExceptionHandler counts into summary.json.
  fParser.SetOverlapCheck(fOverlapCheck);
  fParser.Read(fFile, false);  // no schema validation (needs network access)
  G4VPhysicalVolume* world = fParser.GetWorldVolume();
  if (world == nullptr) {
    G4ExceptionDescription msg;
    msg << "no world volume in " << fFile;
    G4Exception("DetectorConstruction::Construct", "gdmlvar001", FatalException, msg);
  }
  return world;
}

void DetectorConstruction::ConstructSDandField()
{
  G4SDManager* sdm = G4SDManager::GetSDMpointer();
  const G4GDMLAuxMapType* auxMap = fParser.GetAuxMap();
  G4int attached = 0;
  for (const auto& entry : *auxMap) {
    G4LogicalVolume* lv = entry.first;
    for (const auto& aux : entry.second) {
      if (aux.type != "SensDet" || aux.value.empty() || aux.value == "None") {
        continue;
      }
      auto sd = dynamic_cast<EdepSD*>(sdm->FindSensitiveDetector(aux.value, false));
      if (sd == nullptr) {
        sd = new EdepSD(aux.value);
        sdm->AddNewDetector(sd);
        Recorder::Instance().AddDetector(sd);
      }
      SetSensitiveDetector(lv, sd);
      Recorder::Instance().AddDetectorVolume(aux.value, lv);
      ++attached;
    }
  }
  if (attached == 0) {
    G4Exception("DetectorConstruction::ConstructSDandField", "gdmlvar002", JustWarning,
                "no SensDet auxiliary in the GDML file: no detector will be recorded");
  }
}
