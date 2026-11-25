#include "EdepSD.hh"

#include <cmath>

#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4Track.hh"
#include "G4VTouchable.hh"

EdepSD::EdepSD(const G4String& name) : G4VSensitiveDetector(name) {}

void EdepSD::Initialize(G4HCofThisEvent*)
{
  fEdep.clear();
  fUncollided = false;
}

G4bool EdepSD::ProcessHits(G4Step* step, G4TouchableHistory*)
{
  const G4StepPoint* pre = step->GetPreStepPoint();

  const G4double edep = step->GetTotalEnergyDeposit();
  if (edep > 0.) {
    fEdep[pre->GetTouchableHandle()->GetCopyNumber()] += edep;
  }

  // Primary entering this detector with the energy and direction it was
  // generated with: it has crossed everything in front without interacting.
  if (!fUncollided && pre->GetStepStatus() == fGeomBoundary) {
    const G4Track* track = step->GetTrack();
    if (track->GetParentID() == 0) {
      const G4double e0 = track->GetVertexKineticEnergy();
      const G4bool sameEnergy = std::abs(pre->GetKineticEnergy() - e0) <= 1.e-9 * e0;
      const G4bool sameDirection =
        pre->GetMomentumDirection().dot(track->GetVertexMomentumDirection()) > 1. - 1.e-12;
      if (sameEnergy && sameDirection) {
        fUncollided = true;
      }
    }
  }
  return true;
}
