# Click Documentation

Click is a Python package for creating beautiful command line interfaces in a composable way with as little code as necessary. It's the "Command Line Interface Creation Kit". It's highly configurable but comes with sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun while also preventing any frustration caused by the inability to implement an intended CLI API.

Click in three points:
- arbitrary nesting of commands
- automatic help page generation
- supports lazy loading of subcommands at runtime

## Basic Example

What does it look like? Here is an example of a simple Click program:

```python
import click

@click.command()
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name',
              help='The person to greet.')
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        click.echo(f"Hello {name}!")

if __name__ == '__main__':
    hello()
```

And what it looks like when run:

```bash
$ python hello.py --count=3
Your name: John
Hello John!
Hello John!
Hello John!
```

It automatically generates nicely formatted help pages:

```bash
$ python hello.py --help
Usage: hello.py [OPTIONS]

  Simple program that greets NAME for a total of COUNT times.

Options:
  --count INTEGER  Number of greetings.
  --name TEXT      The person to greet.
  --help           Show this message and exit.
```

## Installation

You can get the library directly from PyPI:

```bash
pip install click
```

## Documentation Structure

### Tutorials
- [Quickstart](https://click.palletsprojects.com/en/stable/quickstart/)
- [Virtualenv](https://click.palletsprojects.com/en/stable/virtualenv/)

### How to Guides
- [Packaging Entry Points](https://click.palletsprojects.com/en/stable/entry-points/)
- [Setuptools Integration](https://click.palletsprojects.com/en/stable/setuptools/)
- [Supporting Multiple Versions](https://click.palletsprojects.com/en/stable/support-multiple-versions/)

### Conceptual Guides
- [Why Click?](https://click.palletsprojects.com/en/stable/why/)
- [Click Concepts](https://click.palletsprojects.com/en/stable/click-concepts/)

### General Reference
- [Parameters](https://click.palletsprojects.com/en/stable/parameters/)
- [Parameter Types](https://click.palletsprojects.com/en/stable/parameter-types/)
- [Options](https://click.palletsprojects.com/en/stable/options/)
- [Options Shortcut Decorators](https://click.palletsprojects.com/en/stable/option-decorators/)
- [Arguments](https://click.palletsprojects.com/en/stable/arguments/)
- [Basic Commands, Groups, Context](https://click.palletsprojects.com/en/stable/commands-and-groups/)
- [Advanced Groups and Context](https://click.palletsprojects.com/en/stable/commands/)
- [Help Pages](https://click.palletsprojects.com/en/stable/documentation/)
- [User Input Prompts](https://click.palletsprojects.com/en/stable/prompts/)
- [Handling Files](https://click.palletsprojects.com/en/stable/handling-files/)
- [Advanced Patterns](https://click.palletsprojects.com/en/stable/advanced/)
- [Complex Applications](https://click.palletsprojects.com/en/stable/complex/)
- [Extending Click](https://click.palletsprojects.com/en/stable/extending-click/)
- [Testing Click Applications](https://click.palletsprojects.com/en/stable/testing/)
- [Utilities](https://click.palletsprojects.com/en/stable/utils/)
- [Shell Completion](https://click.palletsprojects.com/en/stable/shell-completion/)
- [Exception Handling](https://click.palletsprojects.com/en/stable/exceptions/)
- [Unicode Support](https://click.palletsprojects.com/en/stable/unicode-support/)
- [Windows Console Notes](https://click.palletsprojects.com/en/stable/wincmd/)

### API Reference
- [API](https://click.palletsprojects.com/en/stable/api/)
  - [Decorators](https://click.palletsprojects.com/en/stable/api/#decorators)
  - [Utilities](https://click.palletsprojects.com/en/stable/api/#utilities)
  - [Commands](https://click.palletsprojects.com/en/stable/api/#commands)
  - [Parameters](https://click.palletsprojects.com/en/stable/api/#parameters)
  - [Context](https://click.palletsprojects.com/en/stable/api/#context)
  - [Types](https://click.palletsprojects.com/en/stable/api/#types)
  - [Exceptions](https://click.palletsprojects.com/en/stable/api/#exceptions)
  - [Formatting](https://click.palletsprojects.com/en/stable/api/#formatting)
  - [Parsing](https://click.palletsprojects.com/en/stable/api/#parsing)
  - [Shell Completion](https://click.palletsprojects.com/en/stable/api/#shell-completion)
  - [Testing](https://click.palletsprojects.com/en/stable/api/#testing)

## Key Features

- **Composable**: Commands can be nested and grouped
- **Automatic Help**: Generates help pages automatically
- **Type Safety**: Built-in parameter type validation
- **Lazy Loading**: Supports lazy loading of subcommands
- **Testing**: Built-in testing utilities
- **Shell Completion**: Automatic shell completion support
- **Unicode Support**: Full unicode support
- **Cross-platform**: Works on Windows, macOS, and Linux

## Core Decorators

- `@click.command()` - Creates a command
- `@click.group()` - Creates a command group
- `@click.option()` - Adds an option to a command
- `@click.argument()` - Adds an argument to a command
- `@click.pass_context` - Passes the Click context to the function

## Parameter Types

Click supports various parameter types:
- `click.STRING` - String type (default)
- `click.INT` - Integer type
- `click.FLOAT` - Float type
- `click.BOOL` - Boolean type
- `click.UUID` - UUID type
- `click.File()` - File type
- `click.Path()` - Path type
- `click.Choice()` - Choice from a list
- `click.IntRange()` - Integer within a range
- `click.FloatRange()` - Float within a range
- `click.DateTime()` - DateTime type
- `click.Tuple()` - Tuple type

## Advanced Features

- **Context Objects**: Share data between commands
- **Custom Types**: Create custom parameter types
- **Callbacks**: Execute code before/after commands
- **Plugins**: Extend Click with plugins
- **Progress Bars**: Built-in progress bar support
- **Color Support**: Terminal color support
- **Paging**: Automatic paging for long output 