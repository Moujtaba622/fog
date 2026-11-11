# FogEdit — Project Overview

## 1. Project Name

**FogEdit — Distributed Fog-Cloud Video Editing Platform**

FogEdit is a web-based video editing and processing platform designed to demonstrate the use of **Fog Computing, Cloud Computing, Big Data, and distributed systems** in a practical application.

The platform allows users to upload videos, perform editing operations, and obtain processed videos while the computational workload is dynamically distributed across three Fog Nodes.

---

## 2. Problem

Video processing can require significant computational resources, especially for large or high-resolution videos.

In a traditional centralized architecture, users send their videos to a central cloud service:

```text
User
  │
  ▼
Cloud
  │
  ▼
Video Processing
  │
  ▼
Result

```

This approach can create:

- high processing load on the central infrastructure;
- unnecessary network traffic;
- increased waiting time when many users submit jobs simultaneously;
- dependence on a centralized processing service;
- inefficient resource utilization when some processing resources are idle.

FogEdit explores whether distributing video-processing workloads across nearby Fog Nodes can improve the behavior of the system.

---

## 3. Proposed Solution

FogEdit distributes video-processing workloads across **three physical Fog Nodes**.

Each Fog Node is an independent computing machine capable of:

- receiving video-processing jobs;
- processing videos;
- maintaining a local job queue;
- monitoring its resources;
- storing local metadata;
- communicating with the other Fog Nodes;
- accepting workloads from other Fog Nodes when it has available resources;
- continuing local operation when another Fog Node becomes unavailable.

A scheduling mechanism considers the current state of the Fog Nodes when deciding where a job should be processed.

The general concept is:

```text
                    Users
                      │
                      ▼
                FogEdit Web App
                      │
                      ▼
                 Job Scheduler
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Fog 1        Fog 2        Fog 3
          ▲           ▲           ▲
          └───────────┼───────────┘
              Fog-to-Fog Cooperation
                      │
                      ▼
                    Cloud
                      │
                Big Data Analysis

```

---

## 4. Video Editing Functionality

FogEdit will provide a web interface through which users can create video-processing projects.

The initial editing functionality may include:

- video upload;
- trimming and cutting;
- merging video segments;
- resizing;
- video compression;
- changing video format;
- changing playback speed;
- adding text;
- adding images or logos;
- adding background audio;
- extracting audio;
- generating thumbnails;
- exporting the final video.

The exact set of editing operations can evolve during development.

The video-processing engine will execute the requested operations on the selected Fog Node.

---

## 5. Fog Computing Role

Fog Computing is the central concept of the project.

The three physical computers are treated as **Fog Nodes positioned between the users and the Cloud**.

Instead of sending every video directly to a centralized Cloud processor, FogEdit attempts to perform processing within the Fog layer.

For example:

```text
User
 │
 │ Video processing request
 ▼
Fog Scheduler
 │
 ├── Fog 1
 ├── Fog 2
 └── Fog 3
       │
       ▼
   Local Processing
       │
       ▼
      Result

```

The Fog Nodes are not simply three independent servers.

They cooperate by exchanging information about:

- CPU utilization;
- memory utilization;
- queue size;
- active jobs;
- node availability;
- processing capacity;
- other information required for workload decisions.

This allows the system to make workload-placement decisions based on the current state of the distributed Fog infrastructure.

---

## 6. Fog-to-Fog Cooperation

A major objective of FogEdit is to demonstrate cooperation between Fog Nodes.

For example:

```text
Fog 1
CPU: 90%
Queue: 12 jobs

Fog 2
CPU: 30%
Queue: 2 jobs

Fog 3
CPU: 60%
Queue: 5 jobs

```

If Fog 1 receives a new expensive video-processing task, it can determine that processing the task locally may be inefficient.

The task can instead be assigned or transferred to Fog 2.

The Fog Nodes can therefore cooperate through mechanisms such as:

- resource-state sharing;
- load-aware job assignment;
- workload migration;
- work sharing;
- failure detection;
- job redistribution after a node failure;
- limited sharing of cached data or processing results.

The communication mechanism will intentionally remain simple. FogEdit is primarily a project about **distributed workload management and Fog Computing**, not about developing a complex network communication protocol.

---

## 7. Cloud Computing Role

The Cloud is not intended to perform every video-processing operation.

Instead, it provides centralized capabilities that are more appropriate for global or long-term processing.

Possible Cloud responsibilities include:

- storing aggregated system information;
- storing historical processing data;
- collecting Fog Node metrics;
- performing large-scale analytics;
- analyzing workload behavior;
- maintaining long-term statistics;
- supporting Big Data processing.

The Fog layer therefore handles primarily **local and time-sensitive processing**, while the Cloud handles **global and historical processing**.

---

## 8. Big Data Role

Video processing generates a large amount of operational data.

For every processing job, the system can record information such as:

```text
Job ID
Video size
Video resolution
Video duration
Requested operations
Fog Node
Processing time
Queue waiting time
CPU utilization
Memory utilization
Network transfer
Timestamp
Job status
Failure information

```

Over a large number of jobs, these records form a dataset that can be analyzed using Big Data technologies.

The analysis can investigate questions such as:

- Which video operations consume the most resources?
- How does video resolution affect processing time?
- How does video size affect network traffic?
- How does workload distribution affect processing time?
- How does Fog processing compare with centralized Cloud processing?
- How does the system behave when one Fog Node becomes overloaded?
- How does the system behave when a Fog Node fails?

---

## 9. Main Objective

The main objective of FogEdit is:

> **To design and evaluate a distributed Fog-Cloud architecture for web-based video processing in which three Fog Nodes cooperate dynamically to distribute computational workloads.**

The project should demonstrate how Fog Computing can be used to move processing closer to users while allowing distributed resources to cooperate.

---

## 10. Evaluation

FogEdit will not only implement the architecture. It will also evaluate its behavior.

A central experiment will compare:

### Centralized processing

```text
Users
  │
  ▼
Cloud
  │
  ▼
Video Processing

```

with:

### Fog-based processing

```text
Users
  │
  ▼
Fog Layer
 ┌────┬────┬────┐
 │ F1 │ F2 │ F3 │
 └────┴────┴────┘
       │
       ▼
Local Processing
       │
       ▼
     Cloud

```

Possible evaluation metrics include:

- average processing time;
- queue waiting time;
- response time;
- throughput;
- CPU utilization;
- memory utilization;
- network traffic;
- Cloud workload;
- workload distribution between Fog Nodes;
- failed jobs;
- recovery time after a Fog Node failure.

---

## 11. Project Scope

The project focuses on:

- distributed video processing;
- Fog Computing;
- cooperation between three Fog Nodes;
- workload scheduling;
- fault tolerance;
- Cloud integration;
- Big Data analysis;
- experimental evaluation.

The project does **not** aim to reproduce a complete commercial video-editing platform.

The video editor should remain sufficiently simple so that the main focus remains on the distributed Fog-Cloud architecture.

---

## 12. Core Design Principles

FogEdit follows these principles:

### 12.1 Three physical Fog Nodes

The project uses three physical computers, with each computer acting as a Fog Node.

### 12.2 Same software on the Fog Nodes

The three Fog Nodes should use the same Fog Node application.

Differences between nodes should primarily come from configuration and runtime state rather than completely different codebases.

### 12.3 Local processing first

Video processing should preferably happen in the Fog layer rather than automatically being sent to the Cloud.

### 12.4 Cooperation between nodes

The Fog Nodes should be able to share workload and react to changes in resource availability.

### 12.5 Simple communication

Communication between Fog Nodes should remain simple and reliable. The project should not become primarily a networking-protocol project.

### 12.6 Measurable behavior

The architecture should generate measurable data so that the benefits and limitations of Fog-based processing can be evaluated experimentally.

### 12.7 Incremental development

The system should first work with a single Fog Node, then be extended to multiple simulated nodes, and finally deployed across the three physical computers.

---

## 13. Final Concept

FogEdit combines a practical application with a distributed-computing research problem.

The user sees a simple web-based video editor.

Behind the interface, the system contains three cooperating Fog Nodes that dynamically manage video-processing workloads.

The Cloud provides global storage and Big Data analytics.

The overall concept is:

```text
             ┌───────────────────────┐
             │        CLOUD          │
             │                       │
             │ Big Data / Analytics  │
             │ Historical Information│
             └───────────▲───────────┘
                         │
                         │
              Global / Historical Data
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │  FOG 1  │◄────►│  FOG 2  │◄────►│  FOG 3  │
   │         │      │         │      │         │
   │ Process │      │ Process │      │ Process │
   │ Queue   │      │ Queue   │      │ Queue   │
   │ Monitor │      │ Monitor │      │ Monitor │
   └────▲────┘      └────▲────┘      └────▲────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                    Web Users

```

**FogEdit is therefore not simply a video editor with three servers. The video editor is the application used to demonstrate a distributed Fog Computing architecture where three nearby computing nodes cooperate to process workloads efficiently.**