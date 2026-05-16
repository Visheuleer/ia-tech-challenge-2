from enum import Enum


class AttendanceType(str, Enum):
    OBSTETRIC_EMERGENCY = "obstetric_emergency"
    DOMESTIC_VIOLENCE = "domestic_violence"
    HORMONAL_MEDICATION = "hormonal_medication"
    POSTPARTUM_CARE = "postpartum_care"


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