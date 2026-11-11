# FogEdit — System Architecture

## 1. Purpose

This document defines the technical architecture of FogEdit.

FogEdit is composed of four main layers:

1. **Web Application Layer**
2. **Fog Computing Layer**
3. **Cloud Layer**
4. **Big Data / Analytics Layer**

The architecture is designed around three physical computers acting as Fog Nodes.

The three Fog Nodes use the same application code but operate with different node configurations and runtime states.

---

## 2. High-Level Architecture

```text
                         ┌──────────────────────────┐
                         │       WEB CLIENT         │
                         │                          │
                         │  Video Editor Interface  │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │     APPLICATION/API      │
                         │                          │
                         │ Project & Job Management │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │     FOG SCHEDULER        │
                         │                          │
                         │ Job Placement Decisions  │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
             ┌────────────┐    ┌────────────┐    ┌────────────┐
             │   FOG 1    │◄──►│   FOG 2    │◄──►│   FOG 3    │
             │            │    │            │    │            │
             │ Processing │    │ Processing │    │ Processing │
             │ Queue      │    │ Queue      │    │ Queue      │
             │ Storage    │    │ Storage    │    │ Storage    │
             │ Monitoring │    │ Monitoring │    │ Monitoring │
             └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
                   │                  │                  │
                   └──────────────────┼──────────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │          CLOUD           │
                         │                          │
                         │ Global Data / Storage    │
                         │ Historical Information   │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │    BIG DATA ANALYTICS    │
                         │                          │
                         │ Historical Analysis      │
                         │ System Metrics           │
                         │ Workload Analysis        │
                         └──────────────────────────┘

```

---

# 3. Web Application Layer

The Web Application is the user-facing part of FogEdit.

Users interact with FogEdit through a browser.

The interface provides:

- project creation;
- video upload;
- video preview;
- timeline;
- editing operations;
- job submission;
- processing progress;
- final video download/export.

The Web Application does not need to perform the heavy video processing itself.

Instead, it creates a description of the requested editing operations and submits a processing job to the backend/Fog infrastructure.

Example:

```json
{
  "projectId": "project-123",
  "videoId": "video-456",
  "operations": [
    {
      "type": "trim",
      "start": 0,
      "end": 30
    },
    {
      "type": "resize",
      "width": 1280,
      "height": 720
    },
    {
      "type": "add_audio",
      "file": "music.mp3"
    }
  ]
}

```

The actual video processing is performed by a Fog Node.

---

# 4. Application/API Layer

The API layer acts as the entry point between the Web Application and the distributed processing infrastructure.

Its responsibilities include:

- receiving user requests;
- creating projects;
- creating processing jobs;
- validating requests;
- tracking job status;
- providing processing progress;
- returning results;
- communicating with the Fog scheduling system.

The API should not contain the actual video-processing implementation.

Instead:

```text
API
 │
 ├── receives request
 │
 ├── creates job
 │
 └── sends job to scheduler
             │
             ▼
        Fog Scheduler

```

This separation keeps the application logic independent from the video-processing infrastructure.

---

# 5. Fog Computing Layer

The Fog layer consists of **three physical computers**.

Each computer runs the same Fog Node software.

```text
┌─────────────────────────────────────────────────────┐
│                  FOG COMPUTING LAYER                │
│                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐│
│  │    FOG 1    │   │    FOG 2    │   │    FOG 3    ││
│  │             │   │             │   │             ││
│  │ Node Service│   │ Node Service│   │ Node Service││
│  │ Job Queue   │   │ Job Queue   │   │ Job Queue   ││
│  │ Processor   │   │ Processor   │   │ Processor   ││
│  │ Monitoring  │   │ Monitoring  │   │ Monitoring  ││
│  │ Storage     │   │ Storage     │   │ Storage     ││
│  └─────────────┘   └─────────────┘   └─────────────┘│
│          ▲                ▲                ▲        │
│          └────────────────┼────────────────┘        │
│                   Fog Cooperation                  │
└─────────────────────────────────────────────────────┘

```

Each Fog Node is capable of operating independently.

However, the nodes can cooperate when distributing workloads.

---

# 6. Fog Node Internal Architecture

Every Fog Node follows approximately the same internal structure.

```text
Fog Node
│
├── API / Node Service
│
├── Job Manager
│
├── Scheduler Interface
│
├── Job Queue
│
├── Video Processor
│      └── FFmpeg
│
├── Local Storage
│
├── Metadata Database
│
├── Monitoring
│
└── Fog Communication

```

### API / Node Service

Provides endpoints for:

- receiving jobs;
- checking node health;
- retrieving job status;
- retrieving results;
- communicating with other Fog Nodes.

### Job Manager

Controls the lifecycle of a processing job:

```text
RECEIVED
   ↓
QUEUED
   ↓
PROCESSING
   ↓
COMPLETED

```

or:

```text
PROCESSING
   ↓
FAILED

```

### Job Queue

Jobs waiting for processing are placed into a queue.

The queue allows the node to process multiple requests without blocking the API.

### Video Processor

The processor performs the actual video operations.

Examples:

- trim;
- merge;
- resize;
- compression;
- format conversion;
- audio extraction;
- text overlay;
- speed modification;
- thumbnail generation.

FFmpeg is responsible for the low-level video processing.

### Local Storage

Temporary and processed video files can be stored locally on the Fog Node.

Large video files should not be stored directly inside MongoDB by default.

### Metadata Database

MongoDB stores information about:

- projects;
- videos;
- jobs;
- processing status;
- node information;
- metrics;
- processing history.

### Monitoring

Each node monitors its own state, including:

- CPU usage;
- RAM usage;
- queue length;
- active jobs;
- available storage;
- processing time;
- node availability.

### Fog Communication

This component handles communication with other Fog Nodes.

The communication layer should remain simple and isolated from the rest of the application.

---

# 7. Relationship Between the Three Fog Nodes

The three nodes are peers within the Fog layer.

They are not three different applications.

```text
Same Codebase
     │
     ├──────────────┬──────────────┐
     ▼              ▼              ▼
  Fog 1           Fog 2           Fog 3

```

Their differences come primarily from configuration:

```text
Fog 1:
NODE_ID=fog-1
NODE_ADDRESS=...

Fog 2:
NODE_ID=fog-2
NODE_ADDRESS=...

Fog 3:
NODE_ID=fog-3
NODE_ADDRESS=...

```

Runtime conditions will naturally differ.

For example:

```text
Fog 1 → CPU 85%, Queue 10
Fog 2 → CPU 35%, Queue 2
Fog 3 → CPU 60%, Queue 5

```

The same software can therefore make different decisions depending on the current state of each node.

Detailed cooperation mechanisms are defined in:

`03_FOG_COOPERATION.md`

---

# 8. Job Flow

A typical video-processing request follows this process:

```text
1. User
      │
      ▼
2. Web Application
      │
      ▼
3. API
      │
      ▼
4. Create Processing Job
      │
      ▼
5. Fog Scheduler
      │
      ├───────────┬───────────┐
      ▼           ▼           ▼
    Fog 1       Fog 2       Fog 3
      │           │           │
      └─────── selected node ──┘
                  │
                  ▼
             Job Queue
                  │
                  ▼
             Video Processor
                  │
                  ▼
               FFmpeg
                  │
                  ▼
             Processed Video
                  │
                  ▼
               Result
                  │
                  ▼
             Web Application
                  │
                  ▼
                User

```

---

# 9. Job Placement

The system should not blindly send every job to the same Fog Node.

The scheduler can consider:

- current CPU usage;
- current memory usage;
- queue length;
- number of active jobs;
- estimated processing time;
- video size;
- network transfer cost;
- availability of required files;
- node availability.

A simplified decision can be:

```text
New Job
   │
   ▼
Check Fog 1
Check Fog 2
Check Fog 3
   │
   ▼
Estimate processing cost
   │
   ▼
Select suitable Fog Node

```

The exact scheduling algorithm will be defined and tested during development.

---

# 10. Fog-to-Fog Communication

Fog Nodes can communicate directly over the local network.

The communication should use a simple and well-defined interface.

Examples of operations include:

```text
GET  /health
GET  /status
POST /jobs
GET  /jobs/{job_id}
GET  /results/{job_id}

```

The purpose of this communication is primarily:

- checking node availability;
- exchanging resource information;
- transferring jobs when required;
- checking job status;
- retrieving processing results.

The system should avoid unnecessary communication.

Fog Nodes should not continuously exchange large amounts of data just to maintain synchronization.

The detailed rules are defined separately in `03_FOG_COOPERATION.md`.

---

# 11. Data Storage Architecture

The project separates **large video files** from **metadata**.

Conceptually:

```text
Video Files
     │
     ├── Fog local storage
     └── Cloud/object storage when required

Metadata
     │
     └── MongoDB

```

MongoDB stores information such as:

```text
Project
Video
Job
Fog Node
Processing Metrics
Processing History

```

A video record may contain:

```json
{
  "videoId": "video-123",
  "projectId": "project-10",
  "filename": "example.mp4",
  "size": 850000000,
  "duration": 240,
  "resolution": "1920x1080",
  "location": "fog-2"
}

```

---

# 12. Cloud Layer

The Cloud is responsible for centralized functions that benefit from global visibility.

Possible responsibilities include:

- long-term storage;
- aggregated metrics;
- historical processing information;
- global project information;
- system-wide analytics;
- Big Data processing.

The Cloud should not be required for every local Fog decision.

For example, a Fog Node should be able to determine whether it is overloaded without asking the Cloud.

This maintains the distinction between the Fog and Cloud layers.

---

# 13. Big Data Layer

The Fog Nodes generate operational data during video processing.

This data can be sent or aggregated in the Cloud.

```text
Fog 1 ──┐
Fog 2 ──┼──► Cloud Data Layer ──► Big Data Analytics
Fog 3 ──┘

```

The analytics layer can process historical information about:

- processing times;
- job sizes;
- video resolutions;
- Fog utilization;
- network transfers;
- queue waiting times;
- failures;
- workload distribution.

This information can be used to evaluate and improve the Fog scheduling strategy.

---

# 14. Failure Model

The system should assume that individual Fog Nodes can become unavailable.

For example:

```text
Fog 1    ✓
Fog 2    ✗
Fog 3    ✓

```

The remaining nodes should be able to continue processing new jobs.

The system can detect failures through health checks or heartbeats.

After detecting a failure:

```text
Fog 2 DOWN
     │
     ▼
Identify affected jobs
     │
     ▼
Redistribute recoverable jobs
     │
     ├──► Fog 1
     └──► Fog 3

```

Failure handling should remain simple enough to test reliably.

---

# 15. Physical Deployment

The final deployment uses three physical computers.

```text
                 Local Network
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
     PC 1          PC 2          PC 3
     Fog 1         Fog 2         Fog 3

```

All three computers run the same Fog Node software.

Configuration identifies each node.

The project should first be developed and tested locally before deployment across the three physical machines.

---

# 16. Development Strategy

The architecture is intentionally designed so that most of the system can be developed without requiring three computers.

### Stage 1 — Single Fog Node

```text
Web App → Fog 1 → FFmpeg → Result

```

Implement and test:

- video processing;
- jobs;
- queue;
- database;
- API.

### Stage 2 — Multiple Local Nodes

Run three Fog Node instances on one computer:

```text
localhost:8001 → Fog 1
localhost:8002 → Fog 2
localhost:8003 → Fog 3

```

Test:

- scheduling;
- job transfer;
- node monitoring;
- failure handling.

### Stage 3 — Three Physical PCs

Move the three nodes onto the actual computers:

```text
PC 1 → Fog 1
PC 2 → Fog 2
PC 3 → Fog 3

```

The application architecture remains the same.

Only the node configuration and network addresses change.

---

# 17. Architectural Principles

FogEdit follows several important architectural principles.

### Same Fog Node software

All three Fog Nodes use the same codebase.

### Configuration over duplicated code

Node identity and network information are configuration values rather than separate implementations.

### Simple communication

Fog-to-Fog communication is isolated and kept intentionally simple.

### Local autonomy

A Fog Node should be able to process jobs locally without depending on the Cloud for every operation.

### Distributed cooperation

Nodes can cooperate when workload distribution or failure recovery requires it.

### Separation of concerns

Video processing, scheduling, communication, storage, monitoring, and analytics should remain separate components.

### Measurability

Important system actions should generate metrics that can later be analyzed.

---

# 18. Architectural Summary

FogEdit can be summarized as:

```text
                        ┌─────────────────┐
                        │    WEB CLIENT   │
                        │  Video Editor   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   API / Backend │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Fog Scheduler   │
                        └────────┬────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             ▼                   ▼                   ▼
        ┌──────────┐        ┌──────────┐        ┌──────────┐
        │  FOG 1   │◄──────►│  FOG 2   │◄──────►│  FOG 3   │
        │          │        │          │        │          │
        │ Process  │        │ Process  │        │ Process  │
        │ Queue    │        │ Queue    │        │ Queue    │
        │ Storage  │        │ Storage  │        │ Storage  │
        │ Monitor  │        │ Monitor  │        │ Monitor  │
        └────┬─────┘        └────┬─────┘        └────┬─────┘
             │                   │                   │
             └───────────────────┼───────────────────┘
                                 │
                                 ▼
                         ┌─────────────────┐
                         │      CLOUD      │
                         │ Global Storage  │
                         │ Historical Data │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  BIG DATA /     │
                         │    ANALYTICS    │
                         └─────────────────┘

```

The architecture therefore separates the system into:

**Users → Application → Fog → Cloud → Big Data**

with the three Fog Nodes cooperating primarily for **local workload distribution, processing, resource awareness, and fault recovery**.