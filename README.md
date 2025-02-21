# Neve

Neve is a modern, hybrid-paradigm programming language designed to deliver reliability through static typing, while providing users a soothing* syntax to work with.

> We are currently working on rewriting the Neve compiler in Kotlin.  Progress can be tracked on the `feature/rewrite-compiler-in-kt` branch.

## Example

```rb
idea Nat = Int | self >= 0

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

The next feature on the horizon for the Neve compiler is **Tables (hash tables)**.

## How to compile a Neve program

> The Neve compiler only compiles simple expressions as of now.

To compile a Neve program, you can simply run:

```
python3.12 -m nevec <file>
```
