#include "VoxelMessenger.hh"

#include <fstream>
#include <iomanip>
#include <map>
#include <sstream>
#include <vector>

#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4Navigator.hh"
#include "G4ScoringManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4TransportationManager.hh"
#include "G4UIcommand.hh"
#include "G4UIdirectory.hh"
#include "G4UIparameter.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VScoringMesh.hh"

VoxelMessenger::VoxelMessenger()
{
  fDir = new G4UIdirectory("/gdmlvar/");
  fDir->SetGuidance("gdmlvar commands.");

  fVoxeliseCmd = new G4UIcommand("/gdmlvar/voxelise", this);
  fVoxeliseCmd->SetGuidance("Write the material at the centre of each cell of a box");
  fVoxeliseCmd->SetGuidance("scoring mesh, in /score/dumpQuantityToFile order.");
  auto param = new G4UIparameter("meshName", 's', false);
  fVoxeliseCmd->SetParameter(param);
  param = new G4UIparameter("fileName", 's', false);
  fVoxeliseCmd->SetParameter(param);
  fVoxeliseCmd->AvailableForStates(G4State_Idle);
}

VoxelMessenger::~VoxelMessenger()
{
  delete fVoxeliseCmd;
  delete fDir;
}

void VoxelMessenger::SetNewValue(G4UIcommand* command, G4String value)
{
  if (command == fVoxeliseCmd) {
    std::istringstream is(value);
    G4String meshName, fileName;
    is >> meshName >> fileName;
    Voxelise(meshName, fileName);
  }
}

void VoxelMessenger::Voxelise(const G4String& meshName, const G4String& fileName)
{
  G4ScoringManager* sm = G4ScoringManager::GetScoringManagerIfExist();
  G4VScoringMesh* mesh = (sm != nullptr) ? sm->FindMesh(meshName) : nullptr;
  if (mesh == nullptr || mesh->GetShape() != G4VScoringMesh::MeshShape::box) {
    G4ExceptionDescription msg;
    msg << "no box scoring mesh named " << meshName;
    G4Exception("VoxelMessenger::Voxelise", "gdmlvar010", JustWarning, msg);
    return;
  }
  const G4ThreeVector half = mesh->GetSize();
  const G4ThreeVector centre = mesh->GetTranslation();
  G4int n[3];
  mesh->GetNumberOfSegments(n);

  G4VPhysicalVolume* world = G4TransportationManager::GetTransportationManager()
                               ->GetNavigatorForTracking()
                               ->GetWorldVolume();
  G4Navigator navigator;
  navigator.SetWorldVolume(world);

  std::ofstream out(fileName);
  if (!out) {
    G4ExceptionDescription msg;
    msg << "cannot write " << fileName;
    G4Exception("VoxelMessenger::Voxelise", "gdmlvar011", JustWarning, msg);
    return;
  }
  out << "# ix, iy, iz, material_id (-1 = outside the world)\n";

  std::map<const G4Material*, G4int> ids;
  std::vector<const G4Material*> materials;
  const G4double step[3] = {2. * half.x() / n[0], 2. * half.y() / n[1], 2. * half.z() / n[2]};
  for (G4int ix = 0; ix < n[0]; ++ix) {
    for (G4int iy = 0; iy < n[1]; ++iy) {
      for (G4int iz = 0; iz < n[2]; ++iz) {
        const G4ThreeVector p(centre.x() - half.x() + (ix + 0.5) * step[0],
                              centre.y() - half.y() + (iy + 0.5) * step[1],
                              centre.z() - half.z() + (iz + 0.5) * step[2]);
        G4VPhysicalVolume* pv = navigator.LocateGlobalPointAndSetup(p, nullptr, false, true);
        G4int id = -1;
        if (pv != nullptr) {
          const G4Material* mat = pv->GetLogicalVolume()->GetMaterial();
          auto it = ids.find(mat);
          if (it == ids.end()) {
            id = static_cast<G4int>(materials.size());
            ids[mat] = id;
            materials.push_back(mat);
          }
          else {
            id = it->second;
          }
        }
        out << ix << ',' << iy << ',' << iz << ',' << id << '\n';
      }
    }
  }
  out.close();

  std::ofstream legend(fileName + ".json");
  legend << std::setprecision(10) << "[\n";
  for (std::size_t i = 0; i < materials.size(); ++i) {
    legend << "  {\"id\": " << i << ", \"name\": \"" << materials[i]->GetName()
           << "\", \"density_g_cm3\": " << materials[i]->GetDensity() / (g / cm3) << "}"
           << (i + 1 < materials.size() ? ",\n" : "\n");
  }
  legend << "]\n";
}
