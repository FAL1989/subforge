Introducing the Claude Code Subagent Dream Team
0:00
It is no secret that Claude code sub
0:02
agents have changed the game for AI
0:04
coding. And today I'll show you how I
0:06
use them along with Archon to build an
0:08
AI agent factory. All I have to do is
0:11
describe at a high level the agent I
0:12
want to create. And then Claude Code
0:14
spins up an entire agentic workflow with
0:17
specialists to help me plan, create, and
0:20
validate my agent. It's a template that
0:22
I have available for you. And right now
0:23
I'll show you how it works. Now sub
0:25
agents are really just prompts. So it's
0:27
not anything new, but the highly
0:29
structured approach that we have to
0:30
define and execute them in cloud code is
0:33
a thing of beauty. With sub agents, we
0:35
get specialized agentic coders to handle
0:38
different parts of our development
0:39
workflow. And then with archon, we use
0:41
it to give knowledge to these sub aents
0:44
and to split the tasks between them. We
0:46
become the project manager of our
0:48
agents. And that my friend is the future
0:50
of agentic coding. So here is the sub
Subagent Workflow Architecture for Creating AI Agents
0:53
agent Asian factory template that I have
0:55
available for you in GitHub linked
0:57
below. You can take this and run with it
0:59
right now to build any agent that you
1:01
want. And the reason that I'm jumping
1:02
into this right now is because there is
1:04
a really helpful diagram in the readme
1:06
here to help us understand this agentic
1:08
workflow that I've created. And so very
1:10
simply, we have all of our sub aents
1:13
that we're using in this workflow
1:14
defined in ourcloud agents folder. These
1:17
are all markdown documents. I'll show
1:18
you how we create these in a little bit.
1:20
So that defines each of our sub aents
1:22
and then in our global rules and claw.md
1:24
I define the workflow exactly what order
1:27
we want to invoke these sub aents how we
1:29
want to do it like we want to invoke
1:31
some of them in parallel also speaking
1:32
to how we can use archon to help us
1:34
manage our knowledge and tasks if you
1:36
have the archon mcp server connected to
1:38
cloud code so we start with our user
1:41
request that goes into our primary cloud
1:44
code agent so no sub aents at this point
1:46
that's going to ask some clarifying
1:47
questions understand our requirements
1:49
and then set up all the tasks in archon,
1:52
distributing it between our different
1:53
sub aents and then it'll immediately
1:55
start prompting our planner. So we have
The Planner Subagent
1:58
our podantic AI planner because pyantic
2:00
AI is the framework that I'm using for
2:02
this factory and it's going to based on
2:04
the requirements given from our primary
2:06
cloud code agent. That's the prompt
2:08
coming into our sub agent. It's going to
2:10
do some web research, look at the Pantic
2:12
AI documentation in Archon, use all of
2:14
that to help it create architecture and
2:16
best practices around the agent we want
2:18
to create, and then it'll output a
2:20
markdown document with its plan. We
2:23
definitely need to have a markdown
2:24
document outputed, and I'll show you we
2:26
have that in our planning folder right
2:27
here. So, it's going to create this uh
2:29
initial MD because remember sub aents
2:33
have their own context window. We don't
2:35
share conversation history between our
2:37
sub agents and our primary cloud code
2:39
agent. So we use these markdown files to
2:41
allow these sub aents to communicate
2:44
with each other and with our primary
2:46
cloud code agent. And so after we go
2:49
through the planning, then our primary
2:51
cloud code agent is going to kick off
The Parallel Subagents (Prompts, Tools, Dependencies)
2:53
three parallel sub aents. We're going to
2:55
plan the system prompt for our agent.
2:58
We're going to plan the different tools
2:59
that we need. And then we're also going
3:01
to plan the package dependencies and
3:03
also the agent dependencies, things like
3:06
API keys and database connections. And
3:08
so it's going to output, again going
3:09
back here, these three markdown
3:11
documents with its plan for building out
3:14
each of those. And so now at this point,
3:16
we've done a lot of context engineering.
3:18
We have the initial plan for our agent.
3:20
We know its system prompt. We know the
3:22
tools that we need and generally how
3:23
we're going to implement them, typically
3:24
with some pseudo code and the
3:26
dependencies that we have. So we really
3:28
do have this rich set of context to now
3:30
dive into the implementation. Now we
3:32
don't have an implementation specific
3:34
sub agent. This just goes to the primary
3:37
cloud code agent to write out all the
3:39
code for us. Then we prompt the
The Validator Subagent
3:42
validator agent. And this is so crucial.
3:44
You always want to allow cloud code in
3:46
some way to validate its own work and
3:49
iterate on the things that it creates
3:50
like unit tests. And so our validator
3:52
sub agent is responsible for that. And
3:55
then after it creates all of its tests,
3:56
it's going to output a validation
3:58
report. We're going to make sure we're
4:00
good there. And then we will deliver the
4:01
final agent. So that is the workflow
Orchestrating the Subagents with Global Rules
4:04
that we have. And like I said,
4:06
everything here is orchestrated within
4:08
the global rules that we have defined in
4:09
our claw.md. So I speak to the trigger
4:12
here like this is when you should invoke
4:14
the sub agent workflow. I talk about
4:16
using archon and then I have the
4:18
complete workflow built here in the
4:19
different phases that I was just showing
4:21
you in the diagram. And a lot of this
4:23
could be a slash command as well. Slash
4:25
commands are your way to have packaged
4:27
up workflows in cloud code, but I just
4:29
wanted to keep this simple and have it
4:31
in the global rules here along with some
4:33
best practices that I have for building
4:34
agents with Pantic AI. So that's
4:36
everything that we have set up here. Now
4:38
I want to dive into sub agents with
4:40
cloud code a bit more with you. Then
4:42
we'll see this all in action and really
4:44
have things come together. And also I
4:46
just want to say here even if you aren't
4:47
interested in building AI agents with
4:49
cloud code specifically this kind of
4:51
workflow will apply no matter what you
4:54
want to create. And so going back to our
4:56
diagram here let's say you wanted to
4:58
build a front-end application for
4:59
example. Well there's still going to be
5:01
different components of your front end
5:03
that you can split up the planning and
5:04
execution between these different sub
5:06
aents building a similar kind of
5:08
workflow. So I hope this kind of can
5:10
inspire you to just think about how you
5:12
can take a problem like let's build a
5:14
front-end app and let's split it into
5:15
well we got our dependencies and then we
5:17
have our components and then we have our
5:19
CSS right like you can split into these
5:21
different things and plan separately
5:23
just like I'm doing with the system
5:24
prompts tools and dependencies for our
5:26
agents. So as I dive into how we can set
5:29
up these sub aents and coordinate them
5:31
together with global rules or slash
5:32
commands think about how this will apply
5:35
no matter what you want to make. All
How to Build and Use Claude Code Subagents
5:37
right, so let's dive more into the
5:38
specifics of sub aents now. So I've got
5:40
the sub aents page of the cloud code
5:42
docs open right here. It's a great
5:44
resource that I'll also have linked
5:46
below. They got a quick start and they
5:47
also cover the key benefits of sub aents
5:49
which are really important to know. And
5:51
so we've talked about some of this a bit
5:53
already, but we have the specialized
5:54
expertise through the fine-tuned prompts
5:56
that we give each agent in the markdown
5:58
files. We have reusability, like
6:01
literally what I'm doing in this video,
6:02
I'm packaging up these sub aents to give
6:04
to you as a workflow. flexible
6:06
permissions. We can define the tools
6:08
that each sub agent has, even the model
6:09
that it uses like Opus, Sonnet or Haiku.
6:12
And then last but not least, we have the
6:13
whole idea of context preservation.
6:16
There's definitely pros and cons to
6:17
this, but these sub agents do not share
6:20
the conversation history with our
6:21
primary claude code agent. So, we have
6:24
to make sure that we're passing in all
6:25
the context the sub agent needs and then
6:27
outputting everything that our primary
6:29
agent needs. That's why we're working
6:30
with markdown files as output here. But
6:32
it's also very nice because we're
6:34
preventing pollution of the main
6:36
conversation. For example, all of the
6:38
web research and calls to the Archon MCP
6:41
for knowledge that our sub agents are
6:43
doing, that doesn't have to pollute the
6:45
primary conversation for our cloud code
6:48
instance. It's really nice to prevent us
6:50
getting to that point where we have to
6:52
autocompact the conversation in cloud
6:54
code, which is never a good thing and
6:55
leads to a lot of hallucinations. And
6:57
so, we're just keeping our conversation
6:59
very concise and directed. That's what
7:02
sub aents help us with. And to get
7:04
started, there's a couple of different
7:05
ways that we can create our first sub
7:08
agent. The easiest way to do so is with
7:10
the slash agents command. And so going
7:13
back to my IDE here, I have Cloud Code
7:15
open up and I'll just do slash agents.
Creating Our First Subagent
7:17
So I'll go ahead and create a new agent.
7:18
I'll put it in the current project. You
7:20
can also make it global with this second
7:22
option. And then I will have Claude help
7:24
me generate this agent. So just like
7:26
with my agent factory that I have for
7:28
you, we can describe at a high level
7:30
what we want for the sub agent. and
7:31
it'll generate the full markdown that
7:33
it'll put within thecloud/ aents folder.
7:36
And so I can say I want to build a sub
7:39
agent that helps me define system
7:42
prompts for my AI agents in Python. So
7:46
I'll send this in. And now it'll go
7:48
ahead and generate the description, the
7:50
system prompt that we have within our
7:52
sub aents. Like for the validator, for
7:54
example, it's about to generate all of
7:55
this right here. And then there are just
7:57
a couple of other things that we get to
7:58
select once it's done there. So, I will
8:00
come back once we have this generated.
8:03
Next, we get to define the tools that we
8:04
want our sub agent to have access to.
8:06
I'll just do all just to keep it simple
8:08
here. And then we get to pick the model,
8:10
which is another really awesome thing
8:11
with sub aents. If there is a certain
8:13
part of your development workflow
8:15
handled by a sub aent that doesn't need
8:16
as much power in the LLM, you can save
8:18
tokens by using Haiku, for example. So,
8:21
I'll just have a balance here with
8:22
sonnet. Then, I'll pick the color that
8:23
it shows in the CLI when we invoke it.
8:25
Pink looks good here. So, there we go.
8:27
And now this is our system prompt
8:30
engineer. So it's going to create this
8:31
markdown file right here in the agents
8:33
folder. So I'll do enter to save. And
8:35
boom, there we go. We have our system
8:37
prompt engineer. And take a look at
8:38
this. We have everything at the top
8:40
describing our agent. We got the name.
8:42
We have the description, which by the
8:44
way, the description is how our primary
8:46
Claude code agent knows when to call
8:49
upon this sub aent. So it's important to
8:51
have things like examples here as well.
8:53
That's why Claude adds these
8:54
automatically. We define our model and
8:56
the color. And then the rest of this is
8:58
the system prompt. This is where we have
9:00
the specialized instructions for our sub
9:02
agent. And so this is generally what I
9:04
followed when I created all of these
9:07
other sub aents. I've got the name,
9:08
description, tools, and color. We got
9:10
our system prompt. That's our dependency
9:12
manager. Same kind of thing with our
9:13
planner, the tool integrator, the
9:16
validator. So I'm not going to go into
9:17
all these sub aents in great detail
9:19
here, but definitely dive in and take a
9:20
look at these if you want. I put a lot
9:23
of time into kind of iterating on these
9:26
sub agents after I created them with
9:28
slash agents. So I didn't just go with
9:30
whatever it spit out initially. I
9:32
cleaned things up, made it more concise,
9:34
made it fit more into the workflow that
9:36
I also have defined in the claw.md. So
9:39
yeah, really dive into this if you're
9:40
curious how I set up this workflow and
9:42
you want to see how you could adapt this
9:44
to whatever kind of software you want to
9:46
build with the help of cloud code. So
9:48
that's the primary way that you can set
9:50
up your sub agents. It's slash agent for
9:52
each one of them and then iterate on
9:54
them with the help of cloud code after.
Creating Subagents with Archon
9:56
Another strategy that I just want to
9:58
call out really quickly here and I tried
10:00
with this as well and it worked
10:02
extremely well. Just take the URL right
10:04
here for the sub aents docs. Go into
10:06
your archon and I'll have a link right
10:08
here to the intro video where I show you
10:10
how to set up archon if you want this
10:12
for yourself. Go add knowledge and then
10:14
paste in this link. This is going to
10:17
give the entire documentation for cloud
10:19
code including sub aents to our archon
10:22
knowledge base. So now cloud code
10:24
connected to the archon mcp server is
10:27
able to search through the sub aent
10:28
docs. It'll understand how to build
10:30
these markdown files and so that way we
10:32
can actually instruct claude code to
10:34
create all of these sub aents at once.
10:36
So we don't have to do slash agents for
10:39
each one of these and iterate on it. And
10:41
so yeah two approaches here. One of them
10:43
is more simple getting started with how
10:45
cloud code recommends creating your sub
10:46
aents and then another one is
10:48
specifically leveraging archon to build
10:50
all this at once. You can build all
10:51
these sub aents and even help you craft
10:54
the cloud.md
10:56
basically defining how we orchestrate
10:58
all of these agents in a workflow. And
11:01
so that's the key thing here is each of
11:02
these sub aents the system prompt and
11:05
description really describes how this
11:08
agent operates in isolation. When do you
11:10
want to use it? How does it work? And
11:12
then our global rules here, which again,
11:13
this could be a slash command. This
11:15
defines how we use all of these sub
11:17
agents together. The sponsor of today's
Lindy
11:19
video is Lindy, a noode AI agent builder
11:22
that isn't just extremely powerful, but
11:24
it's also very easy to use. Plus, they
11:27
just dropped a massive update. Now,
11:29
Lindy has an agent builder, they have
11:31
team accounts, and now we have
11:33
autopilot. So, Lindy agents have access
11:36
to a computer and a web browser. First
11:38
up, we've got the agent builder. Think
11:40
of it like cursor but for building AI
11:42
agents specifically in Lindy. And so we
11:44
just prompt the agent that we want and
11:46
then it creates the full workflow for us
11:49
as a Lindy automation. So just as an
11:51
example right here I had it build an AI
11:53
agent that performs research on a lead
11:55
and drafts an email in Gmail. So this is
11:57
my conversation just super super simple.
12:00
It was so easy to build this and it
12:02
creates the full agent. So, it has these
12:04
skills here, the tools that it has to
12:06
search the lead with Replexity and draft
12:08
an email for the outreach with Gmail.
12:10
And just as an example here, I'm having
12:12
him research Mark Cuban and draft an
12:14
outreach email. So, it's going to start
12:15
with Replexity, then go to the Gmail
12:17
skill, and then we'll see our draft. And
12:19
boom, there we go. Our conversation is
12:21
done, and we have a draft Mark Cuban.
12:23
Obviously, I'm not going to send this,
12:24
but yeah, this automation is working
12:26
perfectly, and I didn't have to build it
12:28
myself. Next up, we've got Autopilot,
12:30
which gives Lindy the ability to
12:32
actually control your computer just like
12:34
a human would. It unlocks literally
12:36
every integration imaginable. Here you
12:38
can see a Lindy agent monitoring Twitter
12:40
for spam, identifying spammer patterns,
12:43
and automatically blocking without any
12:44
intervention from me. And finally, we
12:47
have team accounts in Lindy now, so I
12:49
can invite people in to collaborate on
12:51
these agents with me and deploy them
12:53
companywide. The automation
12:55
possibilities with Lindy really are
12:56
limitless, especially after their recent
12:58
updates. So, definitely check them out.
13:00
Link in the description to get started
13:02
for free, $20 worth of credits, which is
13:04
definitely enough to experience having a
13:06
full AI agent factory working for your
Markdown for Subagent Communication
13:08
team. Now, the last thing that's really
13:10
important to hit on before we dive into
13:11
a demo, is how we are using markdown
13:13
files to efficiently communicate between
13:16
these different sub aents because none
13:17
of them share the same context. And so
13:20
phase zero after we ask for requirements
13:23
we're going to create a folder within
13:25
here. So when we do a third
13:27
implementation there'll be a third
13:28
folder that's created here. And all of
13:30
the planning documents are going to be
13:32
outputed there. And so going to our
13:34
planner to start things off. We're
13:36
specifically having it output a file
13:39
called initial.md within the planning
13:41
folder of the new agent that we're
13:43
creating. And so just to go to my rag
13:44
agent as the example for you, we have
13:47
this planning folder and this is where
13:48
we're outputting the initial MD. So
13:50
that's a part of our process defining
13:52
the inputs and outputs. And we also
13:54
specify some of this in the markdown
13:56
files for the sub aents themselves but
13:58
also having it here because it's
13:59
orchestrating the full workflow. And
14:01
then going into the parallel agents for
14:02
example with the prompt engineer we're
14:04
telling it your input is the initial MD
14:07
and then your output is going to be
14:09
again within the planning folder a
14:10
prompts.md. So we have the prompt come
14:13
into our engineer agent from the primary
14:17
cloud code instance and we're telling it
14:19
to look in initial MD. So those two
14:21
things together is the context for that
14:23
sub agent. So it reads this as its first
14:25
operation and then it's la the last
14:28
thing that it does is it outputs a
14:29
prompts.mmd and it's the same kind of
14:31
thing for the tool development agent.
14:33
It's got the similar inputs and outputs
14:35
and our dependency configuration agent.
14:38
So that is our way to bring in just the
14:40
context that we need for each sub agent
14:42
and then output just the context that we
14:44
need for the rest of the workflow
14:46
keeping our conversation compact and
14:48
very directed and focused on what we
14:50
need to get done. And then also
14:52
throughout this workflow we're
14:53
describing how we can use archon to
14:56
manage the knowledge and tasks that we
14:57
need for our implementation which also I
15:00
did make that optional because I don't
15:01
want to be one of those people that says
15:03
you have to use my tool. And so I am
15:05
describing what it's like to use archon,
15:07
but only if it is available. And so we
15:08
have that managing the whole workflow as
15:11
well, even assigning different tasks to
15:13
the different sub aents that we have in
15:14
each of our phases here. All right. So
Setting Up Our Project (Archon + Prompt)
15:17
now that we understand how sub agents
15:19
work and how I've set up this workflow,
15:21
now let's get into a demo. Let's see
15:22
this in action. And so what we're going
15:24
to be building here is the full example
15:26
that I have referenced at the top of
15:28
this readme, which by the way, this is
15:30
the readme in GitHub. This is what I'll
15:31
have linked in the description. It's a
15:33
part of the whole context engineering
15:35
intro repository that I've been doing a
15:37
lot of things around context engineering
15:38
for you with recently. So yeah, going
15:40
back here, we're just going to follow
15:42
the instructions in the getting started.
15:44
So we simply have a prompt to request
15:46
our agent. What do we want to build?
15:48
We'll answer some clarifying questions
15:50
that it asks for us. That's a part of
15:52
the workflow in phase zero. And then
15:54
we'll watch the magic. I'll show you in
15:56
real time these different sub aents
15:58
operating. We got the planner, then we
15:59
go into our parallel agents, then the
16:01
implementation, then the validation.
16:03
We'll see it all in action. We'll see
16:04
how it works with Archon as well. It's
16:06
really exciting. And then we'll get our
16:08
agent at the end. Like that's it. It is
16:09
really simple to work with this whole
16:11
template. And it all starts with a super
16:13
simple prompt. And I even have the
16:16
sample prompt as a part of this
16:18
repository for you if you want to see
16:19
the exact prompt that I'm about to
16:21
execute to build the agent that I have
16:24
in the demo here. So, this reference is
16:27
what we're about to build. So, I'll copy
16:29
this prompt. I'll do Ctrl J to open up
16:31
my terminal where I already have Cloud
16:33
Code opened up. And then I'll paste this
16:35
bad boy in. Now, before we run this, I
16:37
do want to set up a couple of things in
16:38
Archon. If you want to be using Archon
16:41
to make your implementation even more
16:43
reliable. And so, going back into the
16:45
browser here, the one thing that I'll
16:47
say is it helps a lot because this
16:50
factory is using Pyantic AI for our AI
16:53
agent framework. It's very helpful to
16:55
have the Pyantic AI documentation. And
16:57
so we have the LLM's-Lful.ext.
17:00
This is all of the Pyantic AI docs
17:02
curated into a single file to give to
17:04
LLM. And so I'll have this linked in the
17:06
description as well. If you want to set
17:07
up Archon, copy this URL, go in and add
17:10
the knowledge and crawl everything for
17:12
Pantic AI. I'm not going to do it now
17:13
because obviously it takes a good amount
17:15
of time to chunk and crawl everything.
17:17
But then you'll have the Pantic AI
17:19
crawled. You'll have about 430 code
17:21
examples if things are looking good. Now
17:23
through MCP, Cloud Code is able to use
17:25
Archon to search through the Pyantic AI
17:27
documentation just to make the
17:29
implementation more reliable. And then
17:31
we also want to create a project here.
17:33
So I'm going to go into my projects tab.
17:35
I already have one project created just
17:37
as I was prepping this for you. So I'm
17:39
going to create a brand new one with a
17:40
kind of a similar name. So new project.
17:42
I'll call this uh hybrid
17:45
search rag agent. And then for the
17:48
description here, I'm just going to
17:49
leave this nice and simple and do the
17:51
same thing as the title. But yeah, I'll
17:52
create this project. And now I'm
17:54
specifically going to tell Cloud Code in
17:56
my prompt to reference this new project.
17:59
So I want it to create all the tasks for
18:01
me. We can even have it so that it
18:03
stores the documents for our different
18:06
sub aents here as well. And I actually
18:08
did that as I was testing my
18:10
implementation earlier. So like we have
18:11
the output from the different sub aents,
18:13
these markdown documents. I actually
18:15
have them outputed and stored in Archon,
18:17
which is just a really cool way to store
18:19
all of the context in a database. So
18:21
even other people that want to use
18:23
archon along with us can reference these
18:25
same things. It's really cool. So yeah.
18:27
All right, we got our project set up
18:28
now. So I'm going to go back into claw
18:30
and I'm actually going to tell it to use
18:31
this project. I'll say use the hybrid
18:34
search rag agent project in archon. So
18:38
I'm just going to be explicit here
18:39
creating the project ahead of time. I
18:41
mean it also will just create it for you
18:43
if you don't have one, but yeah, I just
18:44
wanted to define that since I already
18:46
have a similar project in Archon. So
FULL AI Agent Build with Our Subagent Team + Archon
18:47
there we go. Now we're kicking off the
18:49
build. And because we're saying we want
18:50
to build an agent, that's going to
18:52
trigger the full workflow here. So there
18:54
we go. We're starting with our
18:55
clarifying questions. So off camera, I
18:57
just really quickly typed out answers to
18:59
each of its questions. It just wanted to
19:01
know a couple of things like what kind
19:02
of knowledge are we searching through
19:04
and how exactly do we want the agent to
19:05
output its findings? And so I'll send
19:07
this in. And then it's going to start by
19:10
creating some tasks for us in Archon to
19:12
help us orchestrate the usage of our sub
19:14
agent. So there we go. It's starting by
19:16
checking Archon. We are successfully
19:18
connected to the Archon MCP. And then
19:20
after it creates some tasks, we'll dive
19:22
into our first sub agent, the planner,
19:24
where it's going to output that initial
19:26
MD file. Once it does its planning and
19:29
because we're doing the web research and
19:30
all the Archon knowledge lookups within
19:32
that sub agent, it's not going to
19:34
pollute our conversation. And so I'll
19:36
actually show you really quickly. Uh,
19:38
something I want to call out that's
19:39
really interesting is this workflow is
19:42
actually very similar to the agent tier
19:45
that I had with the original version of
19:48
Archon. So, I turned it more now into
19:49
something where it's like task
19:50
management and knowledge for coding
19:52
assistance. Like this is the layer
19:54
between humans and coding assistants.
19:56
But the old Archon was an AI agent that
19:58
builds other agents. But really, it was
20:00
just a bunch of specialized sub aents
20:02
that I had to find through Langraph and
20:04
Pideantic AI. And so we start with the
20:07
planner and then we have our specialized
20:09
agents for the tools and dependencies
20:11
and prompt. Like this really is a a
20:14
version maybe a bit more of a complex
20:16
version of what we have now with sub
20:18
aents in cloud code. So just a little
20:19
interesting tidbit that I wanted to give
20:21
you there. But yeah, look at this. Now
20:23
we're setting up the tasks in archon.
20:25
And so I'll actually show this here.
20:27
I'll bring back over archon. We have
20:29
requirement analysis and system prompt
20:30
design as the two tasks that's created
20:32
so far. And take a look at this. It even
20:34
has it assigned to the right sub agent.
20:36
So the requirement analysis is done by
20:37
the podantic AI planner and then the
20:39
prompt engineer is doing the system
20:41
prompt design. Absolutely beautiful. And
20:43
it's just going to keep creating more
20:44
and more tasks here. Like I'll show you
20:46
that we have it updated here. Like
20:47
there's even more tasks now. And each
20:49
one is assigned to the right agent. Like
20:51
when we do the actual implementation,
20:53
it's correct here that it's using cloud
20:54
code, the primary coding. We're not
20:56
using a sub agent in this case. So yeah,
20:59
it's creating all the tasks and then
21:00
we'll move on to the planner. So I'll
21:02
skip ahead once we got to that point.
21:04
All right. So it moved the task to doing
21:06
for the planning. So if we go back into
21:09
archon here, we can see that yep, we are
21:11
about to execute the pyantic AI planner
21:13
for requirements analysis. And there we
21:16
go. We got the blue popup here. We're
21:18
calling into this sub agent. And by the
21:21
way, the planner agent is where you
21:23
could integrate the PRP framework or
21:25
something like BMAD if you wanted. I'm
21:27
keeping this simple by just using sub
21:29
aents. So not using a more advanced
21:31
context engineering strategy like PRP,
21:33
but I'm not just ditching PRP. I'm only
21:35
excluding it to keep things simple here.
21:37
But you could definitely like generate a
21:38
PRP as a part of your planner sub agent.
21:41
So yeah, I'll let this go for a while.
21:43
It's going to do a lot of web search.
21:45
It's going to look at the Pantic AI
21:47
documentation through Archon. So it'll
21:49
take its time. I'll pause and come back
21:51
once we move on to the next phase. There
21:53
we go. We completed our planner agent.
21:56
Took 1 minute. Took almost 30,000
21:58
tokens. a lot of research that it did
22:00
for us. And then it updated the task,
22:02
marked it as done in Archon, and now
22:03
it's moving on to invoking our parallel
22:06
agents. So, it's updating all three of
22:07
these tasks to doing. And then in a
22:09
second here, we'll see the fancy colors
22:11
pop up for these three agents all
22:13
running in parallel. And in the
22:15
meantime, oh, there we go. All right.
22:16
Now, it's popping up. So, we got orange
22:17
for our prompt engineer. And so, it's
22:19
taking its time crafting the prompt to
22:21
send into the sub agent. So, it finishes
22:23
that. Now, it moves on to our tool
22:24
integrator. And we can see that these
22:27
these dots right here are not blinking
22:28
yet because it's waiting for all three.
22:30
There we go. Now they're all invoked at
22:32
the exact same time once we have the
22:33
prompts sent into each of them. And now
22:35
they are off doing their own thing each
22:38
rep starting by reading the initial MD
22:40
exactly as we planned. And they're going
22:42
to output markdown files in the end. So
22:44
if we go in the agents folder, go into
22:46
no not rag agent hybrid search agent and
22:48
into the planning folder. Right now
22:50
we've got our initial MD. So this is
22:52
what our planner agent outputed. and
22:53
then each of our parallel agents red.
22:56
And so, yeah, the last thing I'll show
22:57
you really quick is if I go back into
22:59
Archon for task management. Just a
23:01
beautiful thing. So, we completed our
23:02
requirements analysis. Now, we're in
23:04
progress for all three of our sub aents
23:07
that each have a task assigned to them.
23:08
This is a thing of beauty. So, all
23:11
right, I will come back again once our
23:13
parallel agents are done and we've got
23:15
all the files in planning. Okay, this is
23:18
actually blazing fast. like it only took
23:20
a minute here because we just had to
23:22
wait for the slowest parallel agent. And
23:23
now we're already moving on to the main
23:25
implementation. So I'm going to close
23:27
out of the terminal here and show you.
23:28
We got our dependencies. We've got our
23:31
initial MD. We have our prompts. So our
23:33
the system prompt for our agent. And
23:35
then we have the general tools that we
23:36
need for our semantic search and then
23:38
also our hybrid search. So this is
23:40
looking fantastic. This is all the
23:43
context we need now. So going back to
23:45
our primary claude agent and we can see
23:47
this going back into archon here that
23:49
now the current agent cla code is doing
23:52
the implementation. This is not a sub
23:54
agent right now and it's going to be
23:55
reading in all these files. This is our
23:57
complete context engineering. And so
23:59
going back to my terminal, let me scroll
24:01
down. Okay. Yep. So now we're doing some
24:03
rag searches with archon to understand
24:05
padantic AI. How to specifically
24:07
implement the agent that we requested.
24:09
Searching some code examples as well. So
24:11
this is just so cool how we're seeing
24:13
Archon in action, all these other parts
24:15
of context engineering coming into the
24:17
fold with sub aents. So yeah, I'm going
24:19
to come back again once we're done with
24:20
the implementation and we move on to
24:22
that last sub agent for our validator.
Final Result & Agent Demo
24:25
And there we go. We have our complete AI
24:28
agent built for us now. Our hybrid
24:29
search rag agent. So we had the
24:31
validator that ran here actually for
24:33
quite a while because it takes some time
24:35
to iterate on the unit tests to make
24:36
sure everything's polished for us. But
24:38
then it updated everything in archon and
24:40
wrote out some documentation. So you can
24:41
see here that we have all the tasks
24:43
complete now in archon. Take a look at
24:45
that. And so what we built just now that
24:48
actually is the full hybrid search rag
24:50
agent that I linked to at the top of the
24:52
readme. So you can check this out if you
24:54
want. You can look into how it was
24:55
built, learn from it, try the thing
24:57
yourself. It's a fully working AI agent.
24:59
I only had to iterate two times to fix
25:01
it up. So I'll save you the boring
25:03
details of having to iterate on this.
25:05
I'll just show screenshots right here
25:07
really quickly of the things that
25:08
weren't working immediately. Just some
25:10
database type issues that I fixed up in
25:12
two more prompts. So, we threehotted
25:14
this hybrid search agent and the rag
25:16
pipeline already came. But yeah, it's
25:18
super super cool. So, I'll go over and
25:20
show you a demo really quickly. Now,
25:21
I've got my environment already set up.
25:23
So, I'll just run the CLI command like
25:24
we have in the readme here and we can
25:26
just do a quick demo of this thing. So,
25:28
I can say for example, how are AWS and
25:32
Anthropic partnered up? So this is just
25:34
one of the documents that I have in my
25:35
knowledge base from that rag pipeline.
25:37
And yeah, if you guys didn't know, AWS
25:40
is where all of the cloud LLM inference
25:42
is run. It's run on AWS infrastructure.
25:44
Super cool. So yeah, we can just ask
25:46
another question as well. Uh like tell
25:48
me about the cloud wars. Just another
25:50
thing I know is in my knowledge base. So
25:52
yeah, just a quick demo to show you what
25:54
we were able to create thanks to the
25:56
power of this agentic workflow using sub
25:59
agents to have all these specialized
26:01
agents operating in different stages of
26:03
our development. Super super cool. We
26:05
use archon to give all the knowledge
26:08
around pyantic AI and also for the task
26:11
management. So we are project manager
26:12
throughout this entire thing too. Super
26:14
super cool. So, that's everything that
26:16
I've got for this sub aent template
26:19
available for you to try right now. I
26:22
hope that you enjoyed this, got a lot
26:24
out of it. If you appreciated this video
26:25
and you're looking forward to more
26:27
things on AI agents and AI coding, I
26:29
would appreciate a like and a subscribe.
26:31
And with that, I will see you in the
26:33
next video.