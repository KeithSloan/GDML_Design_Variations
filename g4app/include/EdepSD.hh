// Sensitive detector recording, per event:
//   * energy deposited, per copy number of the volume hit;
//   * whether the primary particle entered the detector uncollided
//     (unchanged energy and direction) - used to check attenuation against
//     tabulated coefficients.
#ifndef GDMLVAR_EDEPSD_HH
#define GDMLVAR_EDEPSD_HH

#include <map>

#include "G4VSensitiveDetector.hh"
#include "globals.hh"

class EdepSD : public G4VSensitiveDetector
{
  public:
    explicit EdepSD(const G4String& name);
    ~EdepSD() override = default;

    void Initialize(G4HCofThisEvent*) override;
    G4bool ProcessHits(G4Step* step, G4TouchableHistory*) override;

    const std::map<G4int, G4double>& EventEdep() const { return fEdep; }
    G4bool EventUncollided() const { return fUncollided; }

  private:
    std::map<G4int, G4double> fEdep;  // copy number -> energy (G4 units)
    G4bool fUncollided = false;
};

#endif
