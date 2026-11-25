// /gdmlvar/voxelise MESH FILE
//   Writes the material at the centre of every cell of scoring mesh MESH
//   (a box mesh, not rotated) to FILE as "ix,iy,iz,material_id" lines in the
//   same order as /score/dumpQuantityToFile, plus FILE.json listing each
//   material_id with its name and density.  Lets the scored quantity be shown
//   on top of the geometry exactly as Geant4 sees it.
#ifndef GDMLVAR_VOXELMESSENGER_HH
#define GDMLVAR_VOXELMESSENGER_HH

#include "G4UImessenger.hh"
#include "globals.hh"

class G4UIcommand;
class G4UIdirectory;

class VoxelMessenger : public G4UImessenger
{
  public:
    VoxelMessenger();
    ~VoxelMessenger() override;
    void SetNewValue(G4UIcommand* command, G4String value) override;

  private:
    void Voxelise(const G4String& meshName, const G4String& fileName);

    G4UIdirectory* fDir;
    G4UIcommand* fVoxeliseCmd;
};

#endif
