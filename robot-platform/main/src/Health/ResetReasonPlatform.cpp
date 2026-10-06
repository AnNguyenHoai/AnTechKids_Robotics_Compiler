#include "ResetReasonPlatform.h"

#include "Esp32ResetReasonSource.h"

ResetReasonService& systemResetReasonService() {
    static Esp32ResetReasonSource source;
    static ResetReasonService service(source);
    return service;
}
