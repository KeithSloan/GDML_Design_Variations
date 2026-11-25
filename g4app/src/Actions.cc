#include "Actions.hh"

#include "Recorder.hh"

#include "G4Event.hh"
#include "G4GeneralParticleSource.hh"
#include "G4Run.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction() : fGPS(new G4GeneralParticleSource) {}

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fGPS;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event)
{
  fGPS->GeneratePrimaryVertex(event);
}

void RunAction::BeginOfRunAction(const G4Run*)
{
  Recorder::Instance().BeginRun();
}

void RunAction::EndOfRunAction(const G4Run* run)
{
  Recorder::Instance().EndRun(run);
}

void EventAction::EndOfEventAction(const G4Event* event)
{
  Recorder::Instance().EndEvent(event->GetEventID());
}

void ActionInitialization::Build() const
{
  SetUserAction(new PrimaryGeneratorAction);
  SetUserAction(new RunAction);
  SetUserAction(new EventAction);
}
