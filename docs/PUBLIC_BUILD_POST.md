# Public build post

## Long-form draft

I built **Closeout** for the All Things Agentic Hackathon Taskmaster track.

I created this piece of content for the purposes of entering the All Things
Agentic Hackathon.

Closeout is an autonomous last-mile agent for high-stakes deliverables. It takes
a fragmented project workspace, maps requirements to evidence, runs bounded
checks and reversible repairs, preserves external blockers, and seals the result
as a reproducible evidence bundle.

The production design uses a React/FastAPI application on Cloud Run, Firestore
for durable state, Cloud Tasks for authenticated background work, and a private
Cloud Run worker using Google ADK with Gemini 3.5 Flash. Model output is structured
and every executable action must pass a deterministic allowlist.

What I care about most is the evidence boundary: generating a video script does
not prove a video is public, and a local build does not prove a cloud deployment.
Closeout automates what it can prove and keeps everything else visibly blocked.

Demo: `[PENDING_PUBLIC_VIDEO_URL]`

Source: `https://github.com/chnoorlee/closeout-agent`

App: `https://closeout-7ejjj4sb5a-uc.a.run.app`

## Social draft

Built Closeout: an autonomous last-mile agent that maps requirements to evidence,
performs policy-bounded repairs, and seals a reproducible audit bundle with Google
ADK, Gemini 3.5 Flash, Cloud Run, Cloud Tasks, and Firestore.

`[PENDING_PUBLIC_VIDEO_URL]`

#AllThingsAgentic Hackathon

## YouTube upload

**Title:** Closeout - Autonomous Delivery Operations | All Things Agentic Hackathon

**Visibility:** Public

**Description:**

Closeout is an autonomous last-mile agent that maps project requirements to
evidence, performs bounded repairs, preserves external blockers, and seals a
reproducible audit bundle. This continuous live demo shows the public Cloud Run
application dispatching an authenticated Cloud Task to a private worker using
Google ADK 2 and Gemini 3.5 Flash, with durable state in Firestore.

I created this video for the purposes of entering the All Things Agentic
Hackathon.

Live app: https://closeout-7ejjj4sb5a-uc.a.run.app

Source: https://github.com/chnoorlee/closeout-agent

#AllThingsAgentic Hackathon
