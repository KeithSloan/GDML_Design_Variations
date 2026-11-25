#include "CountingExceptionHandler.hh"

G4bool CountingExceptionHandler::Notify(const char* originOfException,
                                        const char* exceptionCode,
                                        G4ExceptionSeverity severity,
                                        const char* description)
{
  ++fCounts[exceptionCode != nullptr ? exceptionCode : "unknown"];
  return G4ExceptionHandler::Notify(originOfException, exceptionCode, severity, description);
}
