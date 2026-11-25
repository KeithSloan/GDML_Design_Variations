// gdmlvar - run one GDML geometry under one reference physics list.
//
//   gdmlvar -g design.gdml -p FTFP_BERT -m run.mac [-s SEED] [-o DIR]
//           [--no-overlap-check]
//
// The geometry comes from the GDML file; volumes with a SensDet auxiliary
// become detectors.  The physics list is any Geant4 reference list name,
// with an optional EM option suffix (FTFP_BERT_EMZ, QGSP_BIC_LIV, ...).
// The macro sets up the source (/gps/...), scoring and /run/beamOn.
// Results: DIR/events.csv and DIR/summary.json (see Recorder.hh).
#include <cstdlib>
#include <iostream>
#include <string>

#include "Actions.hh"
#include "CountingExceptionHandler.hh"
#include "DetectorConstruction.hh"
#include "Recorder.hh"
#include "VoxelMessenger.hh"

#include "G4PhysListFactory.hh"
#include "G4RunManager.hh"
#include "G4RunManagerFactory.hh"
#include "G4ScoringManager.hh"
#include "G4UImanager.hh"
#include "G4VModularPhysicsList.hh"
#include "Randomize.hh"

namespace
{
const char* kVersion = "0.1.0";

void Usage()
{
  std::cerr << "usage: gdmlvar -g FILE.gdml -p PHYSICS_LIST -m MACRO [-s SEED] [-o DIR]\n"
               "               [--no-overlap-check]\n"
               "  PHYSICS_LIST  Geant4 reference list, e.g. FTFP_BERT, QGSP_BIC,\n"
               "                FTFP_BERT_EMZ, FTFP_BERT_LIV\n";
}
}  // namespace

int main(int argc, char** argv)
{
  G4String gdml, physics, macro, outDir = ".";
  long seed = 12345;
  G4bool overlapCheck = true;

  for (int i = 1; i < argc; ++i) {
    const std::string a = argv[i];
    auto next = [&](const char* what) -> std::string {
      if (i + 1 >= argc) {
        std::cerr << "gdmlvar: " << a << " needs " << what << "\n";
        std::exit(2);
      }
      return argv[++i];
    };
    if (a == "-g") gdml = next("a GDML file");
    else if (a == "-p") physics = next("a physics list name");
    else if (a == "-m") macro = next("a macro file");
    else if (a == "-s") seed = std::atol(next("a seed").c_str());
    else if (a == "-o") outDir = next("a directory");
    else if (a == "--no-overlap-check") overlapCheck = false;
    else if (a == "-h" || a == "--help") {
      Usage();
      return 0;
    }
    else {
      std::cerr << "gdmlvar: unknown argument " << a << "\n";
      Usage();
      return 2;
    }
  }
  if (gdml.empty() || physics.empty() || macro.empty()) {
    Usage();
    return 2;
  }

  G4PhysListFactory factory;
  factory.SetVerbose(0);
  if (!factory.IsReferencePhysList(physics)) {
    std::cerr << "gdmlvar: '" << physics << "' is not a Geant4 reference physics list\n";
    return 2;
  }

  G4Random::setTheSeed(seed);

  auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::SerialOnly);
  // Replaces the run manager's default handler; counts warnings by code.
  auto* handler = new CountingExceptionHandler;
  G4ScoringManager::GetScoringManager();  // enables /score/ commands

  G4VModularPhysicsList* physicsList = factory.GetReferencePhysList(physics);
  physicsList->SetVerboseLevel(0);

  Recorder& rec = Recorder::Instance();
  rec.SetOutputDir(outDir);
  rec.SetExceptionHandler(handler);
  rec.SetInfo("app_version", kVersion);
  rec.SetInfo("gdml", gdml);
  rec.SetInfo("physics_list", physics);
  rec.SetInfo("macro", macro);
  rec.SetInfo("seed", std::to_string(seed));
  rec.SetInfo("overlap_check", overlapCheck ? "on" : "off");

  runManager->SetUserInitialization(new DetectorConstruction(gdml, overlapCheck));
  runManager->SetUserInitialization(physicsList);
  runManager->SetUserInitialization(new ActionInitialization);

  auto* voxelMessenger = new VoxelMessenger;

  G4UImanager* ui = G4UImanager::GetUIpointer();
  const G4int status = ui->ApplyCommand("/control/execute " + macro);

  delete voxelMessenger;
  delete runManager;
  return status == 0 ? 0 : 1;
}
