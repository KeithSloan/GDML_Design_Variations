// Geometry read from a GDML file.  Every logical volume carrying
// <auxiliary auxtype="SensDet" auxvalue="NAME"/> gets the EdepSD named NAME
// (one SD per name, shared by all volumes that use it).
#ifndef GDMLVAR_DETECTORCONSTRUCTION_HH
#define GDMLVAR_DETECTORCONSTRUCTION_HH

#include "G4GDMLParser.hh"
#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

class DetectorConstruction : public G4VUserDetectorConstruction
{
  public:
    DetectorConstruction(const G4String& gdmlFile, G4bool overlapCheck);
    ~DetectorConstruction() override = default;

    G4VPhysicalVolume* Construct() override;
    void ConstructSDandField() override;

  private:
    G4String fFile;
    G4bool fOverlapCheck;
    G4GDMLParser fParser;
};

#endif
