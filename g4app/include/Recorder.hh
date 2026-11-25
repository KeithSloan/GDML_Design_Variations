// Collects results for one run (serial run manager only) and writes
//   events.csv    one line per event: energy per detector, uncollided flag
//   summary.json  run information, per-detector sums and per-copy sums,
//                 volume masses, counts of Geant4 warnings by code
#ifndef GDMLVAR_RECORDER_HH
#define GDMLVAR_RECORDER_HH

#include <fstream>
#include <map>
#include <string>
#include <vector>

#include "globals.hh"

class EdepSD;
class G4LogicalVolume;
class G4Run;
class CountingExceptionHandler;

class Recorder
{
  public:
    static Recorder& Instance();

    void SetOutputDir(const G4String& dir) { fOutDir = dir; }
    void SetInfo(const G4String& key, const G4String& value) { fInfo[key] = value; }
    void SetExceptionHandler(const CountingExceptionHandler* h) { fHandler = h; }

    void AddDetector(EdepSD* sd);
    void AddDetectorVolume(const G4String& sdName, G4LogicalVolume* lv);

    void BeginRun();
    void EndEvent(G4int eventID);
    void EndRun(const G4Run* run);

  private:
    Recorder() = default;

    struct CopySums
    {
        G4double sum = 0.;
        G4double sum2 = 0.;
    };
    struct DetSums
    {
        EdepSD* sd = nullptr;
        std::vector<G4LogicalVolume*> volumes;
        G4double sum = 0.;
        G4double sum2 = 0.;
        G4long nonZero = 0;
        G4long uncollided = 0;
        std::map<G4int, CopySums> copies;
    };

    G4String Path(const G4String& name) const;
    void WriteSummary(const G4Run* run, G4double seconds) const;

    G4String fOutDir = ".";
    std::map<G4String, G4String> fInfo;
    const CountingExceptionHandler* fHandler = nullptr;
    std::vector<G4String> fOrder;  // detector names, in registration order
    std::map<G4String, DetSums> fDets;
    std::ofstream fEvents;
    G4long fNEvents = 0;
    double fStartTime = 0.;
};

#endif
