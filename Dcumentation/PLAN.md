# FogEdit — Development and Experiment Plan

## 1. Purpose

This document defines how FogEdit will be developed, tested, deployed, and evaluated.

The development strategy is designed to minimize unnecessary complexity, especially during the early stages.

The system should not begin with three physical computers and complicated Fog-to-Fog communication.

Instead, development progresses from:

```text
Single Fog Node
      ↓
Multiple simulated Fog Nodes
      ↓
Three physical Fog Nodes
      ↓
Fog cooperation
      ↓
Cloud integration
      ↓
Big Data analysis
      ↓
Experimental evaluation

```

This approach allows most application and video-processing problems to be solved before introducing physical distributed-system problems.

---

# 2. Development Principles

FogEdit follows several development principles.

### 2.1 Build the simplest working system first

The first version should be able to:

```text
Upload Video
     ↓
Create Job
     ↓
Process Video
     ↓
Return Result

```

Only after this works reliably should distributed functionality be introduced.

### 2.2 Isolate Fog communication

Fog-to-Fog communication should be implemented as a separate component.

Problems with networking should therefore remain isolated from:

- video processing;
- job management;
- database logic;
- user interface.

### 2.3 Test locally before using physical machines

Three Fog Nodes should first run as separate processes on one computer.

Example:

```text
localhost:8001 → Fog 1
localhost:8002 → Fog 2
localhost:8003 → Fog 3

```

This allows distributed behavior to be tested without network configuration problems.

### 2.4 Introduce one complexity at a time

The project should not simultaneously introduce:

- video processing;
- three physical computers;
- job migration;
- failure recovery;
- Cloud storage;
- Big Data processing.

Each major feature should first be tested independently.

---

# 3. Development Phases

## Phase 1 — Project Foundation

### Objective

Create the initial project structure and establish the basic development environment.

Tasks:

- create the repository;
- define project structure;
- configure development environment;
- create basic backend;
- create basic frontend;
- establish configuration management;
- establish logging;
- define basic data models.

Expected result:

```text
Web Application
      │
      ▼
Backend

```

No distributed processing is required yet.

---

# 4. Phase 2 — Single Fog Node

### Objective

Create one fully functional Fog Node.

Architecture:

```text
Web App
   │
   ▼
Backend
   │
   ▼
Fog 1
   │
   ▼
FFmpeg
   │
   ▼
Processed Video

```

The Fog Node should support:

- receiving jobs;
- validating jobs;
- creating a queue;
- processing videos;
- tracking job status;
- storing metadata;
- returning results;
- monitoring local resources.

---

# 5. Phase 3 — Video Processing

### Objective

Implement the core video-processing functionality.

Initial operations may include:

- trim;
- cut;
- merge;
- resize;
- compression;
- format conversion;
- audio extraction;
- audio insertion;
- speed modification;
- text overlay;
- thumbnail generation.

Each operation should be represented as a well-defined processing instruction.

For example:

```json
{
  "type": "resize",
  "width": 1280,
  "height": 720
}

```

Multiple operations can be combined into a processing pipeline.

Example:

```text
Input Video
    ↓
Trim
    ↓
Resize
    ↓
Add Audio
    ↓
Compress
    ↓
Output Video

```

---

# 6. Phase 4 — Job Management

### Objective

Create a reliable job lifecycle.

A job should move through clearly defined states:

```text
CREATED
   ↓
QUEUED
   ↓
ASSIGNED
   ↓
PROCESSING
   ↓
COMPLETED

```

Failure path:

```text
PROCESSING
   ↓
FAILED

```

Retry path:

```text
FAILED
   ↓
RETRYING
   ↓
QUEUED

```

Every job should have a unique identifier.

Example:

```text
JOB-000001
JOB-000002
JOB-000003

```

This identifier is used throughout the distributed system.

---

# 7. Phase 5 — Monitoring

### Objective

Make each Fog Node aware of its own resource state.

The node should collect information such as:

```text
CPU usage
Memory usage
Storage availability
Queue size
Active jobs
Completed jobs
Failed jobs
Average processing time

```

Example:

```json
{
  "nodeId": "fog-1",
  "cpuUsage": 67,
  "memoryUsage": 51,
  "queueSize": 4,
  "activeJobs": 2
}

```

This information will later be used by the Fog scheduler.

---

# 8. Phase 6 — Simulated Three-Node Environment

### Objective

Run three Fog Nodes on one computer.

```text
                 Local Machine

        ┌──────────┐
        │  Fog 1   │ :8001
        └──────────┘

        ┌──────────┐
        │  Fog 2   │ :8002
        └──────────┘

        ┌──────────┐
        │  Fog 3   │ :8003
        └──────────┘

```

All three instances use the same code.

Only configuration differs:

```text
Fog 1 → NODE_ID=fog-1
Fog 2 → NODE_ID=fog-2
Fog 3 → NODE_ID=fog-3

```

At this stage, test:

- node health;
- status exchange;
- job submission;
- job routing;
- workload distribution;
- node failure simulation.

---

# 9. Phase 7 — Fog Scheduling

### Objective

Implement the first version of workload-aware scheduling.

The scheduler observes:

```text
Fog 1 → CPU 80%, Queue 8
Fog 2 → CPU 25%, Queue 1
Fog 3 → CPU 55%, Queue 4

```

and selects an appropriate node.

The first scheduler should remain simple.

For example, a score could combine:

```text
CPU utilization
+
Queue size
+
Memory utilization
+
Estimated processing cost
+
Transfer cost

```

The exact formula should be determined experimentally.

The first goal is not to create a mathematically optimal scheduler.

The goal is to create a **working and measurable Fog-aware scheduler**.

---

# 10. Phase 8 — Fog-to-Fog Cooperation

### Objective

Allow Fog Nodes to cooperate after the initial scheduling decision.

Implement progressively:

### Step 1 — State sharing

```text
Fog 1 → Fog 2
Fog 1 → Fog 3

```

Nodes exchange resource information.

### Step 2 — Remote job submission

```text
Fog 1
  │
  │ POST job
  ▼
Fog 2

```

### Step 3 — Queued-job migration

Move jobs that have not started processing.

### Step 4 — Work sharing

An overloaded node can transfer queued work to an underutilized node.

### Step 5 — Work stealing

An idle node can request available work from another node.

Each feature should be tested independently before the next one is added.

---

# 11. Phase 9 — Physical Three-PC Deployment

Once the simulated three-node environment is stable, deploy the nodes onto the three physical computers.

```text
Local Network

PC 1 → Fog 1
PC 2 → Fog 2
PC 3 → Fog 3

```

The same Fog Node software is installed on all three machines.

Only configuration changes:

```text
NODE_ID
NODE_ADDRESS
PORT
STORAGE_PATH

```

The deployment should verify:

- network connectivity;
- health checks;
- status exchange;
- job transfer;
- video transfer;
- result retrieval;
- failure detection.

---

# 12. Phase 10 — Failure Handling

### Objective

Demonstrate that the Fog layer can continue operating when one node becomes unavailable.

Test scenario:

```text
Fog 1 ✓
Fog 2 ✗
Fog 3 ✓

```

The system should:

1. detect that Fog 2 is unavailable;
2. stop sending new jobs to Fog 2;
3. identify recoverable jobs;
4. redistribute jobs when possible;
5. continue processing using Fog 1 and Fog 3;
6. detect when Fog 2 returns;
7. allow Fog 2 to rejoin the system.

---

# 13. Phase 11 — Cloud Integration

### Objective

Introduce the Cloud after the Fog infrastructure is functional.

The Cloud should primarily handle:

- historical data;
- global system information;
- aggregated metrics;
- long-term storage;
- analytics.

The Fog layer should remain capable of making local decisions without depending on the Cloud for every operation.

Architecture:

```text
                 Fog Layer
              /      |      \
             ▼       ▼       ▼
           Fog 1   Fog 2   Fog 3
              \      |      /
               \     |     /
                ▼    ▼    ▼
                  Cloud
                    │
                    ▼
               Data Analysis

```

---

# 14. Phase 12 — Big Data Pipeline

### Objective

Collect enough processing data to analyze the behavior of the system.

Each completed job should generate metrics such as:

```text
Job ID
Fog Node
Video size
Video duration
Video resolution
Operations
Queue waiting time
Processing time
CPU usage
Memory usage
Network transfer
Job status
Timestamp

```

Conceptually:

```text
Fog 1 ──┐
Fog 2 ──┼──► Data Collection ──► Cloud ──► Big Data Processing
Fog 3 ──┘

```

The dataset should grow through repeated processing experiments.

---

# 15. Phase 13 — Web Video Editor

### Objective

Complete the user-facing video editing interface.

The frontend should allow users to:

- upload videos;
- preview videos;
- create editing operations;
- arrange operations;
- submit processing jobs;
- monitor processing status;
- retrieve the final result.

The interface should hide the distributed architecture from normal users.

The user should simply see:

```text
Upload
   ↓
Edit
   ↓
Process
   ↓
Download

```

The Fog infrastructure operates behind the interface.

---

# 16. Testing Strategy

Testing should be divided into several levels.

## 16.1 Unit Tests

Test individual components:

- video operation generation;
- job validation;
- job state transitions;
- scheduler calculations;
- monitoring;
- database operations.

---

## 16.2 Integration Tests

Test interactions between components:

```text
API → Scheduler
Scheduler → Fog Node
Fog Node → FFmpeg
Fog Node → MongoDB
Fog Node → Fog Node

```

---

## 16.3 Distributed Tests

Test the three-node system:

- job distribution;
- workload balancing;
- migration;
- work stealing;
- failure detection;
- recovery.

---

## 16.4 End-to-End Tests

Test the complete workflow:

```text
User
 ↓
Web Application
 ↓
API
 ↓
Scheduler
 ↓
Fog Node
 ↓
FFmpeg
 ↓
Result
 ↓
User

```

---

# 17. Experiment Design

The project should evaluate the architecture experimentally rather than simply demonstrating that it works.

The main comparison should be between:

### Configuration A — Centralized Cloud

```text
Users
  ↓
Cloud
  ↓
Video Processing

```

### Configuration B — Fog + Cloud

```text
Users
  ↓
Fog Scheduler
  ↓
Fog 1 / Fog 2 / Fog 3
  ↓
Cloud Analytics

```

The same workloads should be used when possible.

---

# 18. Experiment 1 — Single Job Processing

### Objective

Measure the processing behavior of an individual video.

Record:

- video size;
- resolution;
- duration;
- operation type;
- processing time;
- CPU utilization;
- memory utilization.

Repeat with different video characteristics.

---

# 19. Experiment 2 — Increasing Number of Jobs

### Objective

Study system behavior as workload increases.

Example:

```text
10 jobs
25 jobs
50 jobs
100 jobs
250 jobs

```

Measure:

- average waiting time;
- average processing time;
- throughput;
- queue length;
- CPU utilization.

Compare centralized processing with Fog-based processing.

---

# 20. Experiment 3 — Fog Load Distribution

### Objective

Determine how jobs are distributed across the three Fog Nodes.

Record:

```text
Fog 1 → number of jobs
Fog 2 → number of jobs
Fog 3 → number of jobs

```

Also record:

- CPU utilization;
- queue size;
- processing time.

The purpose is to determine whether the scheduler actually distributes workload according to node conditions.

---

# 21. Experiment 4 — Fog Node Overload

### Objective

Study the behavior of the system when one Fog Node becomes overloaded.

Example:

```text
Fog 1 → artificially overloaded
Fog 2 → available
Fog 3 → available

```

Measure:

- number of jobs transferred;
- queue waiting time;
- processing time;
- resource utilization before and after redistribution.

---

# 22. Experiment 5 — Fog Node Failure

### Objective

Measure the effect of a Fog Node failure.

Example:

```text
Fog 1 ✓
Fog 2 ✗
Fog 3 ✓

```

Measure:

- failure detection time;
- number of affected jobs;
- number of recovered jobs;
- recovery time;
- additional workload on remaining nodes;
- final completion rate.

---

# 23. Experiment 6 — Data Transfer Cost

### Objective

Determine how video transfer affects distributed scheduling.

Test videos of different sizes:

```text
100 MB
500 MB
1 GB
2 GB
4 GB

```

Measure:

- transfer time;
- processing time;
- total job time;
- network traffic.

The purpose is to determine when remote processing is beneficial and when keeping a job local is preferable.

---

# 24. Experiment 7 — Data Locality

### Objective

Measure the effect of already-available data on a Fog Node.

Compare:

```text
Scenario A:
Video already on Fog 1
→ Process locally

```

with:

```text
Scenario B:
Video on Fog 1
→ Transfer to Fog 2
→ Process remotely

```

Measure:

- transfer time;
- total processing time;
- network traffic.

This evaluates whether data locality should influence scheduling decisions.

---

# 25. Experiment 8 — Work Stealing

### Objective

Test whether an idle Fog Node can help an overloaded Fog Node.

Example:

```text
Before:

Fog 1 → Queue 15
Fog 2 → Queue 0
Fog 3 → Queue 2

```

After work stealing:

```text
Fog 1 → Queue 10
Fog 2 → Queue 4
Fog 3 → Queue 3

```

Measure:

- waiting time;
- total completion time;
- workload distribution;
- network traffic.

---

# 26. Experiment 9 — Cooperation Overhead

### Objective

Measure whether Fog cooperation itself introduces significant overhead.

Record:

- number of communication requests;
- communication latency;
- amount of transferred data;
- scheduling time;
- processing time.

The objective is not to maximize communication.

The goal is to determine whether the cooperation mechanisms provide useful benefits relative to their overhead.

---

# 27. Experiment 10 — Large Workload

### Objective

Generate a large number of processing jobs to create a meaningful dataset.

For example:

```text
100
500
1,000
5,000
10,000

```

The exact scale depends on available hardware and processing time.

For each job, collect operational metrics.

The resulting dataset becomes the input for Big Data analysis.

---

# 28. Big Data Analysis

The collected dataset can be analyzed to identify relationships between:

```text
Video Size
      ↓
Processing Time

Resolution
      ↓
CPU Usage

Queue Length
      ↓
Waiting Time

Fog Load
      ↓
Processing Delay

Network Transfer
      ↓
Total Job Time

```

The analysis can also identify workload patterns across the three Fog Nodes.

---

# 29. Main Evaluation Metrics

The project should focus on measurable metrics.

## Performance

- average processing time;
- median processing time;
- total completion time;
- throughput.

## Responsiveness

- queue waiting time;
- request response time;
- job scheduling time.

## Resource Utilization

- CPU;
- RAM;
- storage;
- network bandwidth.

## Distributed Behavior

- jobs per Fog Node;
- migrations;
- work-stealing operations;
- workload imbalance.

## Reliability

- failed jobs;
- recovered jobs;
- failure detection time;
- recovery time.

## Network

- Fog-to-Fog traffic;
- User-to-Fog traffic;
- Cloud traffic;
- video transfer volume.

---

# 30. Important Experimental Principle

The project should not assume that Fog Computing is always faster.

For some workloads, centralized processing may be better.

For other workloads, Fog processing may provide advantages.

The purpose of the experiments is to determine **under which conditions each architecture performs differently**.

For example:

```text
Small Video
     ↓
Network transfer is cheap
     ↓
Remote processing may be practical

```

while:

```text
Very Large Video
     ↓
Network transfer is expensive
     ↓
Local processing may be preferable

```

Similarly, an overloaded Fog Node may benefit from cooperation while a lightly loaded system may gain little from migration.

---

# 31. Expected Development Order

The recommended implementation order is:

```text
1. Project structure
        ↓
2. Backend/API
        ↓
3. Single Fog Node
        ↓
4. FFmpeg processing
        ↓
5. Job queue
        ↓
6. MongoDB metadata
        ↓
7. Monitoring
        ↓
8. Three simulated Fog Nodes
        ↓
9. Scheduling
        ↓
10. Fog-to-Fog communication
        ↓
11. Workload sharing
        ↓
12. Failure recovery
        ↓
13. Three physical PCs
        ↓
14. Cloud integration
        ↓
15. Big Data pipeline
        ↓
16. Web editor completion
        ↓
17. Experiments
        ↓
18. Analysis

```

This order should be treated as the default development plan, but individual steps can be adjusted if implementation results suggest a better sequence.

---

# 32. Definition of a Functional Prototype

A minimum functional prototype should be able to:

```text
✓ User uploads a video
✓ User specifies editing operations
✓ A processing job is created
✓ A Fog Node receives the job
✓ FFmpeg processes the video
✓ The result is returned
✓ Job metadata is stored
✓ Fog resource metrics are recorded

```

At this point, the project is already a functioning video-processing application.

---

# 33. Definition of a Fog Prototype

The Fog prototype should additionally support:

```text
✓ Three Fog Nodes
✓ Same Fog Node software
✓ Node health monitoring
✓ Resource-state sharing
✓ Load-aware job assignment
✓ Fog-to-Fog job transfer
✓ Queued-job migration
✓ Basic failure detection
✓ Basic workload redistribution

```

At this stage, the Fog Computing aspect is operational.

---

# 34. Definition of the Final Prototype

The final prototype should additionally provide:

```text
✓ Web-based video editor
✓ Three physical Fog Nodes
✓ Fog-aware scheduling
✓ Fog-to-Fog cooperation
✓ Failure recovery
✓ Cloud integration
✓ Large-scale metrics collection
✓ Big Data analysis
✓ Experimental comparison

```

The final system should be demonstrable as a complete end-to-end application.

---

# 35. Final Demonstration Scenario

A final demonstration can follow this sequence:

### Step 1 — User uploads a video

```text
User → FogEdit

```

### Step 2 — User performs edits

```text
Trim
Resize
Add audio
Compress

```

### Step 3 — Scheduler evaluates Fog Nodes

```text
Fog 1 → overloaded
Fog 2 → available
Fog 3 → moderate

```

### Step 4 — Job is assigned

```text
Job → Fog 2

```

### Step 5 — Fog 2 processes the video

```text
Fog 2 → FFmpeg → Result

```

### Step 6 — Another workload arrives

Fog 2 becomes overloaded.

```text
Fog 1 ← job
Fog 3 ← job

```

### Step 7 — Fog 2 fails

```text
Fog 2 → DOWN

```

The remaining nodes continue processing.

### Step 8 — Fog 2 returns

```text
Fog 2 → RECOVERING → AVAILABLE

```

### Step 9 — Data is analyzed

Historical metrics are available in the Cloud/Big Data layer.

The system can then demonstrate:

- workload distribution;
- processing performance;
- network behavior;
- failure recovery;
- Fog cooperation;
- historical workload analysis.

---

# 36. Final Project Goal

The development process should result in more than a video editor.

The final objective is to demonstrate a complete distributed Fog-Cloud system:

```text
                         CLOUD
                           │
                    Big Data Analytics
                           │
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       FOG 1            FOG 2            FOG 3
          │                │                │
          └────────────┬───┴───┬────────────┘
                       │
                Fog Cooperation
                       │
                       ▼
                  Video Jobs
                       ▲
                       │
                       │
                    Users

```

The project should demonstrate, through measurable experiments, how a group of cooperating Fog Nodes can be used to distribute video-processing workloads while the Cloud provides centralized historical data management and Big Data analysis.

The key development philosophy is:

> **Build the video-processing system first, distribute it second, make the Fog Nodes cooperate third, and use the resulting data to evaluate the architecture.**

