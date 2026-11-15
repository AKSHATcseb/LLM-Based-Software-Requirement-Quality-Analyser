# Comprehensive Layer 1 Multi-Project & Multi-Version Evaluation Dossier (942 Requirements)

**Generated:** 2026-11-15 18:21:44  
**Evaluation Engine:** Layer 1 Document Understanding & 7-Attribute ISO 29148 Scorer  
**LLM Backend:** `MockLLMClient`  
**Total Scope:** 942 requirements across 43 primary specifications (46 total files evaluated in dataset) in all 15 industrial/academic SRS projects.  

---

## 1. Executive Summary & Aggregate Metrics

- **Total Requirements Tested:** 942 (100.0% of Benchmark Corpus)
- **Total Primary Specifications:** 43 across 15 projects (46 total files evaluated in dataset)
- **Overall Mean Quality Score:** **9.05 / 10.0**
- **Fully Compliant Clean Requirements:** 839 (89.1%)
- **Requirements with Flagged ISO Flaws:** 103 (10.9%)
- **Average Processing Latency:** 0.7 ms per requirement

### ISO/IEC/IEEE 29148 7-Dimension Mean Scores

| Quality Dimension | ISO Weight | Corpus Mean Score | Pass Rate (Score >= 8.0) |
| :--- | :---: | :---: | :---: |
| **Unambiguity** | 20% | **8.98 / 10.0** | 99.4% |
| **Completeness** | 20% | **8.94 / 10.0** | 98.4% |
| **Consistency** | 10% | **9.50 / 10.0** | 100.0% |
| **Conformance** | 10% | **9.00 / 10.0** | 100.0% |
| **Correctness** | 10% | **9.50 / 10.0** | 100.0% |
| **Singularity** | 10% | **8.64 / 10.0** | 91.1% |
| **Verifiability** | 20% | **8.98 / 10.0** | 99.4% |

## 2. Project-by-Project Performance Breakdown

| Project | Versions Covered | Reqs Evaluated | Mean Quality Score | Total Candidate Flaws | Compliant Ratio |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1_FROG** | 2 | 108 | **9.04 / 10.0** | 14 | 88.0% |
| **2_SMIRK** | 3 | 12 | **9.10 / 10.0** | 0 | 100.0% |
| **3_ONEM** | 5 | 74 | **9.06 / 10.0** | 7 | 90.5% |
| **4_UIC** | 5 | 142 | **9.00 / 10.0** | 34 | 76.8% |
| **5_EVLA BACKEND SYSTEM REQUIREMENTS** | 4 | 65 | **9.10 / 10.0** | 0 | 100.0% |
| **6** | 6 | 89 | **9.00 / 10.0** | 17 | 82.0% |
| **7** | 2 | 44 | **9.10 / 10.0** | 0 | 100.0% |
| **8** | 3 | 51 | **9.10 / 10.0** | 0 | 100.0% |
| **9** | 2 | 38 | **9.06 / 10.0** | 4 | 89.5% |
| **10** | 2 | 58 | **9.07 / 10.0** | 3 | 94.8% |
| **11** | 2 | 62 | **9.08 / 10.0** | 3 | 95.2% |
| **12** | 2 | 49 | **9.04 / 10.0** | 5 | 89.8% |
| **13** | 2 | 43 | **9.03 / 10.0** | 7 | 83.7% |
| **14** | 3 | 52 | **9.00 / 10.0** | 10 | 80.8% |
| **15** | 3 | 55 | **9.06 / 10.0** | 2 | 96.4% |

## 3. Representative Requirement Evaluations (Sample Across Projects)

| Project | Version | Req ID | Requirement Statement Body | Quality Score | Primary ISO Shortcomings |
| :--- | :--- | :--- | :--- | :---: | :--- |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-001` | In its initial release, FROG will be packaged with a plug-in for Sun SPOTs. | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-002` | In addition, FROG will contain an evaluation mode as well as a demo program for testi... | **8.7** | Singularity |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-003` | Gestures are the entities which shall be modeled as well as recognized by the FROG pr... | **8.7** | Singularity |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-004` | The FROG Project will be a 3D acceleration-based gesture training and recognition sys... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-005` | These will be: Training, Recognition, Evaluation, and Demo. | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-001` | In its initial release, FROG will be packaged with a plug-in for Sun SPOTs. | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-002` | In addition, FROG will contain an evaluation mode as well as a demo program for testi... | **8.7** | Singularity |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-003` | Gestures are the entities which shall be modeled as well as recognized by the FROG pr... | **8.7** | Singularity |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-004` | The FROG Project will be a 3D acceleration-based gesture training and recognition sys... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-005` | These will be: Training, Recognition, Evaluation, and Demo. | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-006` | The system shall provide feedback to each user when a gesture is not recognized or, i... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-007` | Since it is written in Java, FROG will have an obvious need to interact with a Java V... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-006` | Sample Size: Will allow the user to input the sample size for evaluation. iii. | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-007` | The system shall provide a console window or pane at all times to display relevant, u... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-008` | Plug-ins shall be usable to extend the versatility of the software. | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-009` | The Developer’s Guide will help those who might be developing a plug-in or making mod... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-010` | User chooses to train a new gesture set, which will require the naming of the gesture... | **8.7** | Singularity |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-011` | The system shall support modification of the number of HMM states with a default of 8... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-012` | The users currently loaded training session file must contain gestures that share the... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-008` | The system shall allow the user to load an existing training session either to add ad... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-013` | The FROG Project shall be able to recognize gestures with an 80% or better accuracy. | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-014` | Terminal in New Window: Will display the terminal in a separate window for easier man... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-015` | There will be four of these slots in Screen 3.0. | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-009` | There will be four of these slots in Screen 3.0. | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-016` | The system shall support logging of system status, incoming 3D accelerometer data, an... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-010` | The ability to train a new gesture set will not be available if the last one created ... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-011` | The user interface shall be clean and intuitively labeled to promote a high quality l... | **7.8** | Unambiguity; Verifiability/Feasibility |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-017` | The system shall provide the ability for the user to input the sample size (number to... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-018` | The system shall take 3D accelerometer readings from mobile devices as its input. | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-012` | Session Table: Will allow the user to select which gestures are to be part of the eva... | **8.7** | Singularity |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-019` | The complete FROG Project will come with both a User’s Guide and Developer’s Guide. | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-013` | The system shall support modification (albeit limited to certain values) of the numbe... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-014` | Accelerometer-enabled mobile devices must be used with attention to surroundings. | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-020` | The system shall provide real-time feedback of the performance of the recognition sys... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-015` | Support for each mobile device shall be incorporated into a corresponding plug-in for... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-016` | User chooses to train a new gesture set, which will require the naming of the gesture... | **8.7** | Singularity |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-017` | To the side of the terminal there will be controls for the user to select the feedbac... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-018` | Plug-ins shall be usable to extend the versatility of the software. | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-019` | The system shall support a display of available trained gestures in a particular libr... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-020` | In Training mode, there will be the option of displaying the acceleration values of e... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-021` | These documents and more will be delivered to the project sponsor on a DVD on complet... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-022` | Upon clicking this button, the user will be prompted with a standard save file dialog... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-021` | Both k-means and k-means++ will be supported for vector quantization. | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-023` | Save Gesture Set: Will terminate the collection of instances for a gesture set and th... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-024` | As it is exactly derivative of the forward algorithm above, only now using the β func... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-022` | The users currently loaded training session file must contain gestures that share the... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-025` | Choose Log File: Will allow the user to save the contents being posted in the termina... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-023` | Save Gesture Set: Will terminate the collection of instances for a gesture set and th... | **9.1** | None (Clean) |
| 1_FROG | Software_Requirements_Specification_v30 | `REQ-Software_Requirements_Specification_v30-024` | As it is exactly derivative of the forward algorithm above, only now using the β func... | **9.1** | None (Clean) |
| 1_FROG | SRS_v1.1 | `REQ-SRS_v1.1-026` | There shall also be a connection panel in each mode that allows the user to see the s... | **8.7** | Singularity |

---
*Full tabular results containing all 942 records are available in `layer1_multi_project_evaluation_results.csv`.*