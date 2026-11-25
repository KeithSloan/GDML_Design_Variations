// Standard Geant4 exception handling, plus a count of exceptions by code
// (e.g. GeomVol1002 = overlap found by the GDML reader's overlap check).
// Create it after the run manager so it replaces the default handler.
#ifndef GDMLVAR_COUNTINGEXCEPTIONHANDLER_HH
#define GDMLVAR_COUNTINGEXCEPTIONHANDLER_HH

#include <map>
#include <string>

#include "G4ExceptionHandler.hh"

class CountingExceptionHandler : public G4ExceptionHandler
{
  public:
    CountingExceptionHandler() = default;
    ~CountingExceptionHandler() override = default;

    G4bool Notify(const char* originOfException, const char* exceptionCode,
                  G4ExceptionSeverity severity, const char* description) override;

    const std::map<std::string, long>& Counts() const { return fCounts; }

  private:
    std::map<std::string, long> fCounts;
};

#endif
