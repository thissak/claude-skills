# 경로 레퍼런스

## SSOT 소스 (UECsvDataTableConverter)

| 파일 | 경로 |
|------|------|
| 엑셀 SSOT | `E:\UECsvDataTableConverter\250520_FA50M-계층구조_버튼식별_v3.0.xlsx` |
| DataTable 스크립트 | `E:\UECsvDataTableConverter\ue_create_datatable_gameplaytag.py` |
| Mapping 스크립트 | `E:\UECsvDataTableConverter\EquipmentMapping\generate_equipment_mapping.py` |
| 자동화 배치 | `E:\UECsvDataTableConverter\auto.bat` |

## 생성 파일 (Generated)

| 파일 | 경로 |
|------|------|
| DT_ControlData.csv | `E:\UECsvDataTableConverter\Generated\DT_ControlData.csv` |
| FA50M_GameplayTags.ini | `E:\UECsvDataTableConverter\Generated\FA50M_GameplayTags.ini` |
| equipment_mapping.h | `E:\UECsvDataTableConverter\Generated\equipment_mapping.h` |

## 언리얼 프로젝트 대상 경로

| 파일 | 대상 경로 |
|------|----------|
| DT_ControlData.csv | `E:\KAI_VCBT\fa50visualdev_new\DT_ControlData.csv` |
| FA50M_GameplayTags.ini | `E:\KAI_VCBT\fa50visualdev_new\Config\Tags\FA50M_GameplayTags.ini` |
| equipment_mapping.h | `E:\KAI_VCBT\fa50visualdev_new\Source\FA50VisualDev\Public\HostConnector\ReceiverUdp100\Types\equipment_mapping.h` |

## Conda 환경

```bash
conda activate processtree
```

## 수동 실행

```bash
# 전체 자동화
E:\UECsvDataTableConverter\auto.bat

# 개별 실행
cd E:\UECsvDataTableConverter
python ue_create_datatable_gameplaytag.py

cd E:\UECsvDataTableConverter\EquipmentMapping
python generate_equipment_mapping.py
```
