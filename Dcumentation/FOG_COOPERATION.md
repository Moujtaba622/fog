# FogEdit — Fog Node Cooperation

## 1. Purpose

This document defines how the three Fog Nodes cooperate within FogEdit.

The goal is not to create a complex distributed networking system. The goal is to allow the three Fog Nodes to **share workload, exchange resource information, react to failures, and make processing decisions based on the state of the Fog layer**.

The three Fog Nodes use the same software but may have different runtime states.

```text
             Fog Layer

       ┌─────────┐
       │  FOG 1  │
       └────┬────┘
            │
       cooperation
       │         │
       ▼         ▼
 ┌─────────┐ ┌─────────┐
 │  FOG 2  │◄►│  FOG 3  │
 └─────────┘ └─────────┘

```

---

# 2. Cooperation Principles

FogEdit follows these principles:

### 2.1 Same software

All three Fog Nodes run the same Fog Node application.

Differences are primarily configuration and runtime state.

### 2.2 Local autonomy

A Fog Node should be capable of processing jobs locally.

It should not require another Fog Node or the Cloud for every operation.

### 2.3 Cooperation when beneficial

A node communicates with other nodes when cooperation can improve:

- processing time;
- workload distribution;
- resource utilization;
- availability;
- fault recovery.

### 2.4 Simple communication

Communication between nodes should remain lightweight and understandable.

The project should focus on Fog Computing and distributed workload management rather than developing a complicated communication protocol.

### 2.5 Avoid unnecessary data transfers

Large video files should not be moved between nodes without a reason.

The system should consider the cost of transferring a video when deciding whether to migrate a job.

---

# 3. Information Shared Between Fog Nodes

Each Fog Node periodically exposes its current state.

A simplified node state can look like:

```json
{
  "nodeId": "fog-1",
  "status": "available",
  "cpuUsage": 72,
  "memoryUsage": 58,
  "queueSize": 4,
  "activeJobs": 2,
  "availableStorage": 120,
  "timestamp": "..."
}

```

The exact metrics can evolve during implementation.

The purpose is to allow other nodes to answer:

> "Can this Fog Node efficiently accept another job?"

---

# 4. Node States

A Fog Node can have states such as:

```text
AVAILABLE
BUSY
OVERLOADED
UNAVAILABLE
RECOVERING

```

### AVAILABLE

The node has available resources and can accept new work.

### BUSY

The node is processing jobs but remains capable of accepting additional work.

### OVERLOADED

The node has too many queued or active jobs or insufficient resources.

It may request or trigger workload redistribution.

### UNAVAILABLE

The node is unreachable or has failed.

Other Fog Nodes should stop assigning new jobs to it.

### RECOVERING

The node has returned after a failure and is preparing to resume normal operation.

---

# 5. Heartbeats and Health Checks

Fog Nodes need a simple mechanism to determine whether another node is alive.

For example:

```text
Fog 1 ───── heartbeat ─────► Fog 2
Fog 2 ───── heartbeat ─────► Fog 1
Fog 3 ───── heartbeat ─────► Fog 1

```

A heartbeat can contain:

```json
{
  "nodeId": "fog-2",
  "status": "available",
  "timestamp": "..."
}

```

If a node stops responding for a predefined period, the other nodes can mark it as unavailable.

The exact timeout should be configurable rather than hard-coded into the architecture.

---

# 6. Job Assignment

When a new processing job arrives, the system determines where it should execute.

A simplified process is:

```text
New Job
   │
   ▼
Check Fog Nodes
   │
   ├── Fog 1
   ├── Fog 2
   └── Fog 3
   │
   ▼
Evaluate current state
   │
   ▼
Select suitable node
   │
   ▼
Submit job

```

The decision may consider:

- CPU usage;
- memory usage;
- queue size;
- active jobs;
- estimated processing time;
- video size;
- network transfer cost;
- availability of required data;
- node availability.

The first implementation does not need a sophisticated optimization algorithm.

A simple weighted scoring mechanism can be used initially.

---

# 7. Example of Load-Aware Scheduling

Suppose:

```text
Fog 1
CPU: 85%
Queue: 10

Fog 2
CPU: 30%
Queue: 2

Fog 3
CPU: 60%
Queue: 5

```

A new video-processing job arrives.

The scheduler estimates:

```text
Fog 1 → high waiting time
Fog 2 → low waiting time
Fog 3 → medium waiting time

```

The job is assigned to Fog 2.

```text
                 New Job
                    │
                    ▼
                 Scheduler
                    │
             ┌──────┼──────┐
             ▼      ▼      ▼
           Fog 1  Fog 2   Fog 3
             │      ✓      │
             │   selected  │
                    │
                    ▼
                 Process

```

The purpose is to prevent all jobs from accumulating on one Fog Node while other nodes remain underutilized.

---

# 8. Job Migration

A job may initially be assigned to one Fog Node and later moved to another node.

For example:

```text
Fog 1
Queue = 12

```

while:

```text
Fog 2
Queue = 2

```

Fog 1 may determine that a queued job would be processed faster by Fog 2.

The migration process is:

```text
Fog 1
  │
  │ Job migration request
  ▼
Fog 2
  │
  ▼
Accept job
  │
  ▼
Process

```

The migration mechanism should initially focus on **queued jobs** rather than jobs that are already being processed.

This greatly reduces complexity.

---

# 9. Why Queued Jobs Should Be Preferred for Migration

Moving a job that has not started is relatively simple:

```text
QUEUED
  ↓
TRANSFER
  ↓
QUEUED on another node
  ↓
PROCESSING

```

Moving a job that is already being processed is more complicated:

```text
PROCESSING on Fog 1
        ↓
Save processing state
        ↓
Transfer partial data
        ↓
Restore on Fog 2
        ↓
Continue processing

```

The first version of FogEdit should therefore avoid live migration of active FFmpeg processes.

If migration of active jobs is investigated later, it should be treated as an optional advanced feature.

---

# 10. Work Sharing

Fog Nodes can also cooperate when one node has significantly more work than another.

Example:

```text
Before:

Fog 1 → 12 jobs
Fog 2 → 2 jobs
Fog 3 → 4 jobs

```

After workload redistribution:

```text
Fog 1 → 8 jobs
Fog 2 → 5 jobs
Fog 3 → 5 jobs

```

The goal is not necessarily to make the queue sizes identical.

The goal is to avoid severe resource imbalance.

---

# 11. Work Stealing

An alternative mechanism is for an underutilized Fog Node to request work.

Example:

```text
Fog 2:
CPU = 20%
Queue = 0

```

Fog 2 checks other nodes and discovers:

```text
Fog 1:
CPU = 90%
Queue = 10

```

Fog 2 can request a queued job.

```text
Fog 2 ───── "Do you have work?" ─────► Fog 1
Fog 1 ───── "Yes, Job 105" ─────────► Fog 2

```

Fog 2 then processes the job.

This allows idle Fog Nodes to help overloaded nodes.

---

# 12. Avoiding Unnecessary Video Transfers

Video files can be large.

Therefore, workload distribution must consider the cost of transferring the video.

Example:

```text
Video size = 4 GB

```

Suppose:

```text
Local processing:
300 seconds

Transfer + remote processing:
350 seconds

```

The system should keep the job local.

But if:

```text
Local processing:
600 seconds

Transfer + remote processing:
250 seconds

```

Migration becomes more attractive.

The scheduling decision should therefore consider both:

```text
Processing Cost
+
Network Transfer Cost

```

rather than CPU utilization alone.

---

# 13. Local Data and Cache Awareness

A Fog Node may already contain a video or an intermediate result.

For example:

```text
Fog 1
video_123.mp4
video_123_720p.mp4

```

A new job requires:

```text
video_123.mp4

```

Fog 1 already has the required data.

Sending the job to Fog 2 would require transferring the video.

Therefore, the scheduler can prefer Fog 1 even if Fog 2 has more available CPU.

This introduces **data locality** into Fog scheduling.

---

# 14. Result Sharing

Fog Nodes can share information about completed processing results.

For example:

```text
Fog 1
   │
   │ video_123_720p.mp4
   ▼
Result available

```

If another node needs the same result, the system can determine whether it is better to retrieve the existing result or process the video again.

This can reduce unnecessary repeated processing.

---

# 15. Failure Detection

FogEdit assumes that individual Fog Nodes may fail.

Example:

```text
Fog 1 ✓
Fog 2 ✗
Fog 3 ✓

```

The failure can be detected through missed heartbeats or failed health checks.

Once Fog 2 is considered unavailable:

```text
Fog 2
  ↓
UNAVAILABLE

```

New jobs should not be assigned to it.

---

# 16. Recovery After Failure

Suppose Fog 2 was processing:

```text
Job 101 → completed
Job 102 → completed
Job 103 → processing
Job 104 → queued
Job 105 → queued

```

Fog 2 then fails.

The system can recover the jobs whose state is known to be unfinished.

For example:

```text
Fog 2 DOWN
    │
    ├── Job 101 → completed
    ├── Job 102 → completed
    ├── Job 103 → recover/retry
    ├── Job 104 → Fog 1
    └── Job 105 → Fog 3

```

The first implementation should favor **retrying jobs from a known safe state** rather than attempting to recover an interrupted FFmpeg process from the exact point of failure.

---

# 17. Duplicate Processing Protection

A distributed system must avoid accidentally processing the same job multiple times without knowing it.

Every job should have a unique identifier:

```text
JOB-000123

```

The system should maintain job states such as:

```text
CREATED
QUEUED
ASSIGNED
PROCESSING
COMPLETED
FAILED
RETRYING

```

A node should verify the job state before accepting or starting a job.

This reduces the possibility of:

```text
Fog 1 → processing Job 123

Fog 2 → also processing Job 123

```

unless the system explicitly decides that a retry is required.

---

# 18. Communication Interface

Fog Nodes should expose a small set of simple APIs.

Possible interface:

```text
GET  /health

```

Checks whether the node is available.

```text
GET  /status

```

Returns current resource and workload information.

```text
POST /jobs

```

Submits a job to the node.

```text
GET /jobs/{job_id}

```

Returns the current job state.

```text
GET /results/{job_id}

```

Provides information about a completed result.

The exact API can change during implementation.

The important principle is to keep the communication interface **small and well-defined**.

---

# 19. Communication Philosophy

Communication is deliberately not the main research problem.

FogEdit should avoid unnecessary distributed-system complexity.

The system should initially avoid:

- custom network protocols;
- complex peer-to-peer discovery;
- distributed consensus;
- complicated leader-election mechanisms;
- live migration of FFmpeg processes;
- continuous synchronization of large video files.

Instead, the project should use simple communication primitives to support the actual Fog objectives.

The goal is:

> **Simple communication, intelligent workload management.**

---

# 20. Central Scheduler vs Distributed Decisions

FogEdit can use a scheduler to make the initial job-placement decision.

```text
User
 │
 ▼
Scheduler
 │
 ├── Fog 1
 ├── Fog 2
 └── Fog 3

```

The Fog Nodes can then cooperate after assignment when required.

This is preferred for the initial implementation because it keeps the architecture understandable.

A fully decentralized scheduler may be investigated later, but it is not required for the core project.

---

# 21. Example Complete Cooperation Scenario

Consider a user uploading a 2 GB 4K video.

### Step 1 — Job creation

```text
User
 ↓
Web Application
 ↓
Create Job #500

```

### Step 2 — Scheduler checks Fog Nodes

```text
Fog 1
CPU: 80%
Queue: 8

Fog 2
CPU: 25%
Queue: 1

Fog 3
CPU: 55%
Queue: 4

```

### Step 3 — Scheduler estimates cost

```text
Fog 1 → 410 sec
Fog 2 → 150 sec
Fog 3 → 270 sec

```

### Step 4 — Job assigned to Fog 2

```text
Job #500
    ↓
Fog 2

```

### Step 5 — Fog 2 processes the video

```text
Job #500
    ↓
FFmpeg
    ↓
Edited video

```

### Step 6 — Metrics recorded

```text
Job: 500
Node: Fog 2
Processing time: 143 sec
Queue time: 8 sec
CPU average: 71%
Video size: 2 GB

```

### Step 7 — Data sent to Cloud analytics

The processing information becomes part of the historical dataset.

---

# 22. Example Failure Scenario

Suppose Fog 2 becomes unavailable during the next job.

```text
Fog 1 ✓
Fog 2 ✗
Fog 3 ✓

```

The other nodes detect the failure.

The scheduler stops assigning new jobs to Fog 2.

Queued/recoverable jobs are redistributed:

```text
Job 501 → Fog 1
Job 502 → Fog 3
Job 503 → Fog 1

```

Fog 1 and Fog 3 continue operating.

When Fog 2 returns:

```text
Fog 2
   ↓
RECOVERING
   ↓
Health check
   ↓
AVAILABLE

```

It can then rejoin normal operation.

---

# 23. Cooperation Metrics

FogEdit should record metrics specifically related to cooperation.

Examples:

### Workload distribution

```text
Fog 1 → 35%
Fog 2 → 40%
Fog 3 → 25%

```

### Job migrations

```text
Total jobs: 1000
Migrated jobs: 180

```

### Failed jobs

```text
Total failures: 12
Recovered: 11

```

### Network transfer

```text
Fog-to-Fog transfer:
450 GB

```

### Scheduling efficiency

```text
Average queue waiting time:
Before cooperation → 82 sec
After cooperation  → 41 sec

```

These measurements allow the cooperation strategy to be evaluated objectively.

---

# 24. What Cooperation Should Achieve

The cooperation mechanisms are intended to provide:

- better workload distribution;
- reduced queue waiting time;
- better resource utilization;
- continued operation when one node fails;
- reduced unnecessary processing;
- awareness of data locality;
- efficient use of the three Fog Nodes.

The project should measure these effects rather than assuming that cooperation always improves performance.

---

# 25. Core Cooperation Model

The final cooperation model can be summarized as:

```text
                    NEW JOB
                       │
                       ▼
                 ┌───────────┐
                 │ Scheduler │
                 └─────┬─────┘
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
          Fog 1      Fog 2      Fog 3
            │          │          │
            └──────┬───┴───┬──────┘
                   │       │
             State sharing │
                   │       │
                   ▼       ▼
              Workload Cooperation
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    Migration   Work       Failure
                Sharing    Recovery
        │          │          │
        └──────────┼──────────┘
                   ▼
              Video Result

```

The essential idea is:

> **The three Fog Nodes remain independently capable of processing videos, but cooperate whenever sharing workload, information, or resources can improve the overall system.**

The cooperation layer should remain deliberately simple so that the main complexity of the project lies in **Fog-aware video processing and distributed workload management**, rather than in maintaining a complicated communication infrastructure.