# Historical SRS Evolution & Benchmark Report: 1_FROG

## 1. Empirical Change Classification Breakdown (Later Draft -> Final Release)

| Change Taxonomy Category | Count | Type |
| :--- | :---: | :--- |
| **UNCHANGED** | 95 | Baseline / Compliant |
| **EDITORIAL_TEXTUAL** | 3 | Formatting / Superficial |
| **QUALITY_REFINEMENTS** | **0** | **ISO 29148 Quality Repairs** |
| **FUNCTIONAL_SCOPE_CHANGE** | 8 | Business / Feature Scope Shift |
| **REQUIREMENT_ADDED** | 2 | New Capability in Final Release |
| **REQUIREMENT_DELETED** | 2 | Deprecated in Final Release |
| **TOTAL ALIGNED UNITS** | **110** | |

## 2. Pipeline-1 Semantic Correspondence (vs Final SRS Release Ground Truth)

| Evaluation Metric | Observed Value | Description |
| :--- | :---: | :--- |
| **Active Proposals Evaluated** | **0** | Requirements where Pipeline-1 proposed refinements |
| **MATCHED Proposals** | **0** | Independent proposals anticipating the Final SRS specification |
| **PARTIALLY_MATCHED Proposals** | **0** | Flagged correct defect with alternative formulation in Final SRS |
| **NOT_MATCHED Proposals** | **0** | Proposals with no counterpart in Final SRS |
| **Proposal Match Rate (Combined)** | **0.0%** | Proportion of active proposals matched or partially matched |
| **Proposal Match Rate (Strict)** | **0.0%** | Proportion of active proposals strictly matched |
| **Quality Refinement Recall** | **0.0%** | Proportion of Final SRS quality fixes anticipated by Pipeline-1 |
| **Quality Refinement Precision** | **0.0%** | Proportion of active proposals corresponding to Final SRS quality fixes |
| **Overall Evolutionary Agreement** | **20.0%** | Specification-wide agreement across all pairs (incl. true negatives) |

## 3. Itemized Evolution & Evaluation Findings

| Req ID | Working Draft (Input) | Pipeline-1 Refinement | Final Release (Ground Truth) | Historical Category | Correspondence |
| :--- | :--- | :--- | :--- | :---: | :---: |
| REQ-Draft-079 | Exit Training: Will terminate the training session, close screen 2.0, and open screen 1.0. e) Graphical Displays: This panel will show different graphical displays such as a graph of 3D acceleration values as well as the clusters from the k-means algorithm. f) Session Panel: This panel will show the gestures that are part of the current gesture session and allow the user to load an image (using a standard open file dialog) to represent each gesture by clicking on the icon to the right of the current image. g) Terminal: The terminal will serve as the primary method of providing feedback to the user in real-time about the actions being performed, performance etc. | Exit Training: Will terminate the training session, close screen 2.0, and open screen 1.0. e) Graphical Displays: This panel will show different graphical displays such as a graph of 3D acceleration values as well as the clusters from the k-means algorithm. f) Session Panel: This panel will show the gestures that are part of the current gesture session and allow the user to load an image (using a standard open file dialog) to represent each gesture by clicking on the icon to the right of the current image. g) Terminal: The terminal will serve as the primary method of providing feedback to the user in real-time about the actions being performed, performance etc. | The choices of this combo box will correspond to the plug-ins installed. ii. | UNCHANGED | `NOT_MATCHED` |
| REQ-Draft-063 | Code written for the Sun SPOT (i.e. for filtering) shall not hinder its ability to process accelerometer and radio transmission/reception data. | Code written for the Sun SPOT (i.e. for filtering) shall not hinder its ability to process accelerometer and radio transmission/reception data. | Code written for the Sun SPOT (i.e. for filtering) shall not hinder its ability to process accelerometer and radio transmission/reception data. | UNCHANGED | `NOT_MATCHED` |
| REQ-Draft-079 | In Training mode, there will be the option of displaying the acceleration values of each axis and performance of the algorithms involved. | In Training mode, there will be the option of displaying the acceleration values of each axis and performance of the algorithms involved. | The choices of this combo box will correspond to the plug-ins installed. ii. | UNCHANGED | `NOT_MATCHED` |
| REQ-Draft-001 | In its initial release, FROG will be packaged with a plug-in for Sun SPOTs. | In its initial release, FROG will be packaged with a plug-in for Sun SPOTs. | In addition, FROG will contain an evaluation mode as well as a demo program for testing and demonstrating the capabilities of the project. | UNCHANGED | `NOT_MATCHED` |
| REQ-Draft-106 | That is, Demo mode will require a certain set of predefined gestures to be trained within the library chosen. | That is, Demo mode will require a certain set of predefined gestures to be trained within the library chosen. | To utilize Demo mode, an appropriate library must be loaded. | UNCHANGED | `NOT_MATCHED` |