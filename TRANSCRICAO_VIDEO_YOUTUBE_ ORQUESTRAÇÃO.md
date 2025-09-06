hey everyone.
Welcome back to another episode on how to Get the Best Out of Claude
Code Now if you've been following this series for a while, you'll know
that one of the things that I've covered is Claude Code subagents.
after investigating it and looking at how many other people are utilizing it,
I've come up with a pattern that I think is extremely useful whenever you want
to get from an idea and bring it into a first version like an MVP or a prototype.
let me show you a demonstration of what I've built today.
the goal is to take in a YouTube video And generate a social proof widget
that will give you a summary of the overall performance of the video as
well as the sentiment that people have when they look at their comments.
so what I'm gonna do here is open up one of my previous videos and grab the URL.
then I'm gonna hop over here and paste it in this text box.
what happens is that it uses the YouTube API to get hold of the information
and then it uses chat GBT, to then perform sentiment analysis on it.
And here's the result.
it's been able to pull the title from the video.
And you can see some stats about the video themselves.
But here's the interesting part.
it's actually taken in, the comments, sent it to chat GBT, and
then provided a sentiment analysis.
As you can see here, there was quite a positive reaction to that video.
now the thing that I wanted to achieve here is
I didn't want to just generate a report like this.
one of the key features here is that I can actually copy and paste
this as an iframe and it actually serves it up so you can embed this.
In any website that you have, and this is the whole point, why I built this
app, I wanted to be able to use this almost like a service that allows me
to put these widgets onto my website as social proof for specific videos.
And I will be showing you how I built this entire application from a single
PRD file that you see over here.
but one of the most common requests that I've gotten is to showcase
how I got around to building this PRD file in the first place.
So that's what I'll be covering today as well.
Insiders Club
if you're interested in getting hold of the material that I use in today's
tutorial, you might wanna check out my AI oriented Insiders Club.
It's completely free to join, and within it you'll be able to
find material associated with all the videos that I publish.
and this includes full lesson plans for every video that I publish, as well as
access to private GitHub repositories where I post multiple things, including
the source code prompts, subagents, as well as the commands that I use.
Builder Pack
And if you want to take things a step further, you might want to check out
my clock code builder pack, within it you'll be able to find all of the
material that's been related to my entire series related to Clark code.
including all of the subagent, all of the source code for all the apps
that I've built, it also includes all the outputs from the design
and implementation phases as well.
this pack has been very useful in helping people get up and running and
accelerating their clock code journey.
so if this is something that you would like to do, hit on over to
the link in the description below
All right, and without further ado, let's get going with today's tutorial.
all right, So let me give you an overview of the subagent that we'll
be using today along with the command.
Sub-agents: What NOT to do
I'm sure you've seen many repositories or posts by people out there
showing you how you can replace an entire team of developers with
40 to 50 different subagent types.
if you actually dive a little bit deeper, you will very quickly realize that it's
not very practical for day-to-day use.
So I want to show you step by step, a practical way of how you can
make use of subagents this approach is different from one of my early
episodes when Subagent first came out.
Sub-agents: What TO do
first of all, I'm gonna open up my clock folder over here.
You can see I have an agent's folder.
the main thing to focus on is that I will have one orchestrator agent, and this
is the primary agent that's responsible for coordinating across all of the other
subagents and making sure that their output is put into the correct places.
So you will see that I actually have separated the implementation agents
as well as the research agents.
the way that we're gonna do it is just like how I've done it in the past.
I'm gonna do a research space.
In which all of the subagents will be working together, each of them will write
their outputs out into a specific location as determined by the orchestrator.
only then do we move on to the implementation phase.
And during the implementation phase, you will see we will only use one
or two subagents at a time, and they will always be run in sequence.
because you're dictating where the specific locations of the outputs of
these agents are going to be, you can safely run many of them in parallel.
Without worrying about them conflicting with one another.
this is the key pattern to recognize here and has been recommended by
several experts about the best way of utilizing some agents when
you're building your application.
Slash Command: /design-app
Now let's talk about the commands.
We will actually be just making use of two commands here.
The first one is called design app, and this will kick off the design.
From the single PRD that we have, and then we will do the
implementation phase utilizing all of the outputs from the design phase.
if you actually saw the previous video that I just did,
This should be very familiar to you, but, but in today's episode, you
Sub-agents: YouTube & ChatGPT
will realize that we are building something more complex because this
time we have two external services that we have to make use of.
One of them is the YouTube data, API, and the second one is actually interfacing
with chat GBT, if you actually just take a look at both of them here.
I always make sure that they focus on grabbing the documentation first
before performing any actions during the research or planning phase.
I've also added in Some common pitfalls and best practices based on several
runs that I've had utilizing these subagents on building my projects.
and I think this is actually the best way to go about building subagents.
I don't think it's a case where you write one subagent and then
you never update it ever again.
I think it's an iterative process and you should always be updating
your subagent just like how you always update your CLO MD file.
you have to remember that sub-agents always start off with a blank context
apart from the prompt that the master agent sends into it, when it begins.
So you cannot rely on the fact that you've looked up the docs during
the main conversation window.
There's a high chance that the subagent may not remember that
conversation from earlier before.
and the second thing is that because the context always gets clear,
it's very important that they write their outputs into the file system
this allows you to actually have a persistent memory of everything that
the subagents have been performing in relation to your application.
the last thing to mention here is that we have this.
Single PRD file that we will be starting from, and one of the most popular
questions that I've gotten is how do you go about building a PRD file?
so I'm actually gonna showcase it to you right now.
How to PRD
So actually there's no hard and fast rule of how you go about building one.
in fact half the time, I feel that whenever you go to chat GBT and
say build a PRD for something, it ends up being something that is
not really practical for usage.
And I'm gonna show you the process that I used for this app over here,
which I found to be pretty effective.
what I've actually done is that I just opened up clock.
And you can do the same thing with chat, GBT.
rather than saying something like create a PRD for an app that I want to build.
That creates social proofs, you know, yada, yada, yada.
What you should be doing is ask it to create a prom for
you rather than the actual PRD.
And then using that prom that has been optimized, you then
pass it into a PRD creator.
And for example, if you look over here, I have a PRD subagent that is specialized
in building product requirement documents.
So I'm actually gonna be asking Claude to create a prompt for
me to pass into this PRD writer.
So let me just show you the exact thing that I asked Clark to do I did this
with Cloud Opus 4.1, and I said I want you to optimize a prompt for me that
will clearly be used for the purpose of generating a PRD for building a web app.
That, and then this is where I actually pass in all the features given a YouTube
VRL, we'll gather all the details of the video, create a nice looking social proof
element, perform a sentiment analysis.
Using an AI endpoint and then add a carousel of social
proof of positive comments.
And if you actually saw the demo earlier, you can see that
it's actually got all of this.
the first key idea here is that rather than asking straight off the bat for it to
create a PRD for you, ask it to optimize a prom for you to pass into a PRD creator.
And what happened after this is that I took this entire thing and pasted it
into a text file that I had over here.
alright, that was step one.
The second step that I did was to go into cloud and ask it to
read the prompt, create PRD text.
now this is the second stage of optimizing the prom.
this is where you do some back and forth with the AI to continue to
iterate towards something that you want.
because it's in a pro format rather than the PRD itself, you will be able
to quickly spot things that are missing.
For example, the first thing I spotted that was missing.
That I forgot to prompt it about was about having this
embedable widget functionality.
so from there I would just say, consider the prompt in create PRE
doc text and how I can include the ability for my app to provide.
An embed widget on other websites.
the idea here is that you go back and forth with the LLM to continue to
optimize the prompt itself, not the PRD.
And so you can see here, it's actually finished so once you're
happy with your prompt, have, I have this PRD writer agent,
And then I go into my front copy and paste the whole thing in here, and off it goes.
that's the entire process I've done to create that initial PRD file.
I find that this is a much better way to reason about the requirements rather than
iterating on A PRD that gets generated straight off the bat by clock or chat GBT.
and as you can see here, the PRD, the subagent has begun.
And because it's really an expert on PRD writing, and I've already optimized
the prompt that I pass into it.
So the end result is going to be something that's a lot more
robust for implementation.
Design
Alright, so now that we have our PRD documentation over here, we're ready
to get started with the design phase.
I'm going to use this custom command that I created called Design App.
all I need to do is pass in the path to the PRD file.
I'm just gonna kick this off right here so that I can talk about what it's doing
while it's running in the background.
Alright, so you can see that this command has kicked off.
So I'm going to dive deeper into the design app, custom command.
Now, the main thing to take away from here is that This design phase is
gonna run in five phases in total.
first of all, note that the orchestrator will always start the
entire thing and then end off the end.
And the reason for this is that the orchestrator is in charge of making
sure that everything that comes up from the phases in between, whether it's
running sequentially or in parallel, are all stored in the right location.
And this is really important because remember, the way that subagent handle
memory is by writing it to file, okay?
and in between this, you'll see that it'll run a UI design phase
to build up some wire frames.
and then you'll do a third phase where it'll run several subagents
in parallel before synthesizing the results and ending the design phase.
So let's take a look at CLO over here.
I've turned on the explanatory output style because helps explain
things that are going along.
So you can see here the orchestrator is done initializing the project structure.
And I'll show it to you right here.
So what is done is that you can see over here, it's actually created
a project and timestamped it and then it's created a manifest file.
the main goal here is to make sure that everything that is output from all of
the other agents are all tied together and it knows where everything is.
And this is the key thing to enable you to then move on to the
implementation phase afterwards.
Okay, so let's actually just take a look.
the UI designer has kicked off.
you can see it's doing this design specification over here.
And so let's take a look at what is come up with.
because this is a specialized agent, it's been able to create a set
of things that are very important to consider while building this.
It's got a design philosophy, color palette, typography and
many other things as well.
let's scroll down.
You can see that it's laid out what kind of color scheme that it should have.
different styling options, the different components.
and here's the thing that I really like.
it actually creates a wire frame of how it wants everything to look.
And this wire frame approach is actually surprisingly effective in building
really good looking applications.
Sub-agents in parallel
Alright, so let's jump back to cloud over here because the UI
designer has now finished its phase.
this third phase is where everything runs in parallel.
this is the beauty of running a multi-agent architecture
within Claude Code.
You need to know when you want things to run sequentially, but also know
when you can run things in parallel.
because all of these things will be writing their outputs you
do not have to worry about them writing conflicting information or
overriding on top of the application.
And this is why it's really important to separate out your design and planning
phase from your implementation phase.
So what we're gonna do is let these agents all run to completion, and we should start
to see all of the agent outputs appearing within this output folder over here.
Design Pt 2
Okay.
And as you can see right here, we are actually done with
all of the parallel subagent.
It's run all the agents, successfully.
And now the design phase has completed everything from the UI
to the components to the testing architecture and API integrations.
And if you look at the left over here, you can see all of the output.
Of all of the different subagent have been placed over here.
So if you look into how the chat GPT integration is going to be like,
you can actually run through here.
It covers everything from the model selection to the analysis
approach to the target metrics.
and if you look at the chat CN expert, it actually gives you a lot more details
about the specific design elements that you're going to need and the different
components And this is the YouTube data, API one, which tells you how to
deal with the YouTube API, along with the different things like the schema.
now that everything has been output, you will see that it's going to synthesize
and validate everything from all of the subagent and put it into the
manifest file that we have over here.
So what it's going to do, as you can see, it actually just, I think
you just saw it happening live.
It's actually updated this to ensure, according to the checklist that everything
expected from each of these different subagent, from the different, from
the different phases have been output.
And then it's going to ensure that the core functionality requirements based
on the PRD are actually resolved by all of the outputs from the agents.
And this is the reason why having an orchestrator is the design pattern.
That you want to have, because if you tried to run each of these agents
individually or in parallel, but without context of how everything fits together,
you wouldn't end up with a cohesive app.
you would end up with lots of different issues and the reason for that is
because Claude at IT stands currently only has about 200 K contact window.
So there's no way you're gonna be able to squeeze everything into a single run.
So what you want to do is to write all of these outputs to file, and
then use an agent to look through them and review things and then
select things intelligently.
Okay?
Our design phase is now completed.
You can see that we've got all the outputs here and all of the agent
specifications, and we have a central registry with the manifest file.
and now that everything is completed over here, it is time for us
to go ahead and implement it.
Implement
and the way that we implement it is very similar.
if you look over here, I'm just gonna collapse this.
This is an implement app custom command you can see that it takes in the design
outputs from the design app phase.
starting from the manifest, it will look through all the different subagent outputs
and then it will utilize a different set of subagents to implement it.
So let's go ahead and give it a try.
I'm gonna open this up here, and then I'm gonna do implement app.
it says that it wants the design folder output.
And the way that you do it is that you can pass in the manifest file.
And what we want is just the folder.
The next thing you want to do is to pass in the folder in which you
would like this app to be created in.
And I've actually initialized a. Boilerplate next JS app.
Within this app folder.
So I'm just gonna app And let it go.
Okay?
you will see that what happens over here is that it's going to analyze what's in
the app phase, and then it's gonna use the outputs of everything that we have.
it's just gonna start the implementation from the design specifications,
And then you will actually look at the manifest and implement
everything using subagent Alright.
You can see that it's really got the next app over there.
I'm just gonna fast forward this phase so that We can see the end result.
Result
All right, so I'm running this on NPM Run Dev, and here's the app that we've
gotten, and you can see that it's more or less gotten to where we needed it to
be based on what our requirements were.
this is where the main action is going to be, where we put in our YouTube URL,
and then there's a bunch of additional things that it's decided to add on,
and the reason why it's come up with this is that based on the PRD, if you
are not precise it may start to be more creative around what it wants to do.
let's give this a whirl right now.
I'm gonna go over to my channel and pick, one of the videos that I had.
maybe this video.
I'm just gonna grab the URL and then jump back here.
Alright, and so let's just give this a, well, I'm gonna click
generate widget And it's kicked off.
Now you can see it's fetching the video metadata.
So this is using the YouTube data, API.
It's analyzing the top comments.
and now it's done and it's generating the widget.
And here we go.
You can see the widget is ready and so you see it is actually working.
so, it's actually correctly gotten the title and the name of the channel.
it's given you a summary of all the key sets, like the views,
the likes, and the comments.
It's done a sentiment analysis on the comments that were over there, and you
can see that this video was particularly positive the audience highly engaged
and appreciative of the latest cloud good features and tools and also the
practical applications demonstrated.
So if you do agree with that, and hopefully this video does the same
thing for you, Don't forget to give this video a like, subscribe
and turn on those notifications.
Alright?
and so you can see this is actually working really well.
It's got the carousel of the different comments from the
people that is selected as well.
And then it's got this embed code which allows you to embed this widget
onto any website of your choosing.
because this is an I frame over here.
I'm just gonna grab this I'm just gonna paste this into the search
bar and let's see what happens.
Cool.
Alright.
you can see this is the widget that you can then embed onto any website.
this fulfills the requirements that I set up to do and this is really cool.
This means that you can actually now.
Service, like a service whereby people are able to put in any YouTube URL
that they want and then they can embed it onto their website and effectively
you've just created a YouTube social proof SaaS, which is great.
and you can see that the steps that we took here were create A PRD,
perform the design phase, and then perform the implementation phase.
And it's brought you to this stage where you have a really good working MVP.
Caveats
now I need to caveat a few things.
because this is an MVP, it is not quite ready for production, but
this sets a really good foundation for you to start to iterate on.
For example,
Everything that is running is on my local server.
Right now.
It's storing everything in local storage.
if you want to persist this you will need to work with Clot and the app to integrate
this with an external database like Superb Base or your very own Postgres database.
another thing to mention is I hit two issues using this approach.
The first issue was that even though it had all the components to visually
render everything, it forgot to wire up the API calls into the rendering logic.
I had to prompt clock to figure out why it was only serving up mock data and he
managed to fix that with a single problem.
The second thing that it didn't do is that it actually didn't wire
up this widget route to enable me to serve this in this manner.
And so this took another prompt.
for it to actually wire it up.
so after encountering those issues, I went ahead and told Claude to improve
the prompts for both the subagent as well as the design app, custom command.
And I think this is the approach that you should be taking whenever
you're building application.
I don't think you're going to be able to one shot the perfect prompt for
your subagents or for your commands.
But what you need to do is that as you continue to build more and more apps, you
will discover edge cases that is missing.
Then you go ahead improve the prompts or add in another subagent or more.
So one of the things that I did is that I realized it's actually very useful to
have a next GS expert to help deal with next GS 15 related functions because there
were a lot of things that were deprecated.
So the next time when I run this, I'll know it'll do a better job, I think
this outlines the approach that you should be taking when you're working.
I think this method of using a design phase to write things to
output and then implementing it with a second set of subagent.
It's actually very robust.
You can see that this working prototype we have here is actually
a really good foundation for us to continue to build upon.
in fact, if I had made some of those changes to the subagent before it
would've brought me a lot closer to be able to one shot the prototype that
matched the requirements a lot closely.
Outro
alright, so that's it for today's tutorial.
I hope that it's been useful for you.
I think Claude Code and it's sub-agent architecture, when used correctly,
can be extremely powerful when paired with the right commands.
And I hope that this tutorial has shown you the approach that I've been taking
when I'm building my application.
if you enjoyed today's tutorial, don't forget to give it a, like, hit that
subscribe button and turn on notifications so that you're always the first to know
whenever new content like this drops.
And if you want to dive deeper into approach, that can help make
your applications a lot more robust when you're building it using a
test driven development approach.
Check out this video over here that uses the same approach I used today,
but using a custom output style falls clo code into making sure that it was
writing tests for every new feature they was developing, And that is the formula
to reducing 90% of your errors that you usually encounter when you're getting
clock code to do your applications.
so if you're interested to learn more, definitely check out this video.
alright, that's it for today.
I'll see you next time.