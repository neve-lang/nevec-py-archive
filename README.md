# Neve

Neve is a modern, hybrid-paradigm programming language designed to deliver reliability through static typing, while providing users a soothing* syntax to work with.

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

The next feature on the horizon for the Neve compiler is **UTF-16** and **UTF-32 strings**, along with support for UTF-8 ones.

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
