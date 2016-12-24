# Tutorial

This chapter describes the MCDPL modeling language,
which allows the formal definition of co-design problems,
by way of a tutorial.

## Basics

The goal of the language is to represent all and only [MCDPs
(Monotone Co-Design Problems)](#def:MCDP). For example, multiplying by a negative number is a syntax error.
<!-- <footnote>Similarly, CVX's~\cite{cvx} goal
is to describe all only convex problems.</footnote> -->

The interface of each subsystem is specified
by its <f>functionality</f> and its <r>resources</r>.

#### Composition

The language encourages a compositional approach to
co-design.

There are several notions of "compositions"
between two design problems (DPs) for which
MCDPL provides syntactic constructs:

* *series*: two DPs can be connected in series
  if the second provides
  the resources required by the first.
* *parallel*: \xxx
* *co-product*: Two DPs can describe two alternatives
* *recursive*: A larger DPs can be defined as the
  interconnection of smaller, primitive DPs.
* *templating*: \xxx

<col3>
    <span figure-id="Series">series</span>
    <span figure-id="Parallel">parallel</span>
    <span figure-id='Co-product'>co-product \xxx</span>
    <span figure-id='Recursive'>recursive \xxx</span>
    <span figure-id='Templating'>templating \xxx</span>
</col3>

<!--
MCDPL supports a modules system that allows to re-use
commonly used models. -->
<p></p>

#### Querying

After an MCDP has been defined, then it can be "queried". For
example, the user can ask what is the optimal configuration of the
system that has the least amount of resources.

#### Queries

MCDPL comes with a web-based GUI described in <ref>Chapter ???</ref>. The user can input a model and immediately see the graphical representation of such model.
