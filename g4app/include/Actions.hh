// User actions: GPS primary generator, run and event actions forwarding to
// the Recorder.  Serial run manager only.
#ifndef GDMLVAR_ACTIONS_HH
#define GDMLVAR_ACTIONS_HH

#include "G4UserEventAction.hh"
#include "G4UserRunAction.hh"
#include "G4VUserActionInitialization.hh"
#include "G4VUserPrimaryGeneratorAction.hh"

class G4GeneralParticleSource;

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
  public:
    PrimaryGeneratorAction();
    ~PrimaryGeneratorAction() override;
    void GeneratePrimaries(G4Event* event) override;

  private:
    G4GeneralParticleSource* fGPS;
};

class RunAction : public G4UserRunAction
{
  public:
    void BeginOfRunAction(const G4Run* run) override;
    void EndOfRunAction(const G4Run* run) override;
};

class EventAction : public G4UserEventAction
{
  public:
    void EndOfEventAction(const G4Event* event) override;
};

class ActionInitialization : public G4VUserActionInitialization
{
  public:
    void Build() const override;
};

#endif
