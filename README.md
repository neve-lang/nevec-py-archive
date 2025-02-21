# Neve

Neve is a modern, hybrid-paradigm programming language designed to deliver reliability through static typing, while providing users a soothing* syntax to work with.

> We are currently working on rewriting the Neve compiler in Kotlin.  Progress can be tracked on the `feature/rewrite-compiler-in-kt` branch.

## Example

```rb
idea Nat = Int where self >= 0

fun fib(n Nat)
  match n
    | < 2 = n
    | else = fib(n - 1) + fib(n - 2)
  end
end

fun main
  let fib_seq = 0..10 | fib n

  puts fib_seq
end
```

\* Syntactical aesthetics are ultimately subjective, and Neve's syntax may not be considered 'soothing' by everyone.

## What's Next

Implementation of UTF-16 and UTF-32 strings has been delayed; however, Neve now supports UTF-8 strings.

The next feature on the horizon for the Neve compiler will be **named constants**.
Something like this:

```rb
const
  Some = 10

  # optional type annotation
  Thing Int = 20

  Else = 30
end

const Named
  Some = 40
  Thing = 50
  Else = 60
end

# temporary "print" keyword--this won't compile in future updates
print Some + Thing + Else
print Named.Some + Named.Thing + Named.Else
```

However, any PR is welcome, whether it is related to the implementation of
the next feature or something completely different that benefits the project.

## How to compile a Neve program

> The Neve compiler only compiles simple expressions as of now.

To compile a Neve program, you must first install the compiler's requirements:

```
python3.12 -m pip install -r requirements.txt
```

Once the requirements are installed, you may compile your Neve code using:

```
python3.12 -m nevec <file>
```
