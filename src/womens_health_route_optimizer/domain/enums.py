from enum import Enum


class AttendanceType(str, Enum):
    OBSTETRIC_EMERGENCY = "obstetric_emergency"
    DOMESTIC_VIOLENCE = "domestic_violence"
    HORMONAL_MEDICATION = "hormonal_medication"
    POSTPARTUM_CARE = "postpartum_care"


class VehicleType(str, Enum):
    MOTORCYCLE = "motorcycle"
    REFRIGERATED_VEHICLE = "refrigerated_vehicle"
    OPERATIONAL_VAN = "operational_van"


ATTENDANCE_TYPE_LABELS: dict[AttendanceType, str] = {
    AttendanceType.OBSTETRIC_EMERGENCY: "Emergência obstétrica",
    AttendanceType.DOMESTIC_VIOLENCE: "Violência doméstica",
    AttendanceType.HORMONAL_MEDICATION: "Medicamento hormonal",
    AttendanceType.POSTPARTUM_CARE: "Atendimento pós-parto",
}


ATTENDANCE_TYPE_PRIORITIES: dict[AttendanceType, int] = {
    AttendanceType.OBSTETRIC_EMERGENCY: 1,
    AttendanceType.DOMESTIC_VIOLENCE: 2,
    AttendanceType.HORMONAL_MEDICATION: 3,
    AttendanceType.POSTPARTUM_CARE: 4,
}


VEHICLE_TYPE_LABELS: dict[VehicleType, str] = {
    VehicleType.MOTORCYCLE: "Moto de atendimento",
    VehicleType.REFRIGERATED_VEHICLE: "Veículo refrigerado",
    VehicleType.OPERATIONAL_VAN: "Van operacional",
}