# alertbook
An Ansible-inspired Prometheus rules file compiler

## Installation

The recommended installation method is via `pip`:

```
pip install alertbook
```

For development use, clone this repository and install with the `-e`
(development) flag in `pip`:

```
git clone https://github.com/kneitinger/alertbook.git
cd alertbook
pip install -e .
```

## Usage

This program works in analogously to how `ansible-playbook` works.  A
*rulebook* is like an `ansible` playbook, where variables are defined and the
desired rules are listed, each with conditions, or `conds`, under which they
should be instantiated.

A project layout might look something like:
```
alertbook_proj
├── foo_cluster.yml
└── rules
    ├── DiskFailure
    └── DiskUsageHigh
```

By default, the `alertbook` command looks for rules in the `./rules` directory,
and outputs compiled `*.rules` files to the `./out` directory, but these values
can be modified with the `--rules-dir` and `--out-dir` command line arguments,
respectively.


### Rules

_Note: this tool is currently only compatible with the rule format of
Prometheus versions less than 2.0_

The rules files that `alertbook` expects look no different than the recording
and alert rules files that Prometheus already uses...in fact, files in that
format can be included as is into an `alertbook` rules directory.  They can
also be augmented with variables (in the form `${foo}` that can be assigned in
a rulebook. For example, the following rule,

```
ALERT DiskUsageOver${threshold}Percent
    IF node_filesystem_avail / node_filesystem_size < (100 - ${threshold}) / 100
    FOR 5m
    LABELS { severity = "${prio}" }
    ANNOTATIONS {
        description = "{{ $labels.instance }} disk usage has over {$threshold}%."
    }
```

parameterizes the disk usage percentage and alert priority with the
`${threshold}` and `${prio}` variables, meaning that the same rule can be used
in a variety of contexts.


### Rulebooks

A rulebook is a YAML file of the form.

```
---
name: "Text to appear in compiled .rules file header"
vars:
  some_ident: "in scope for all rules unless overwritten"
rules:
  - file: path-relative-to-rules-dir
    conds:
      - some_var_in_rule_file: doop
        another_var_in_rule_file: [8,16]
      - some_var_in_rule_file: floop
        another_var_in_rule_file: 53
```

The `name` component is a purely cosmetic value that populates the header in
the output rules file's header.  The `vars` component allows you to define
global variables for the rulebook.

The `rules` component is where all of the desired rules are listed, and their
variables, if any, are instantiated.  Each entry has a `file` option, which
specifies the path of the file relative to the default or user-specified rules
directory, and optionally, a `conds` list, where any remaining variables are
specified.

#### Conditions
The `conds` list can have many items (conditions), and each item may generate one or
more rules, depending on whether or not a variable is defined as an array.

When a condition's variables only have single element values, `alertbook` fills
the rule's variables in with those values, and adds it to the output text.
When one or more of the condition's variables has an array value, `alertbook`
creates a set of values equal to the Cartesian product of the condition's
variables and outputs one rule for each set.  See the **Example** section for
further clarification.

### Command

```
$ alertbook -h
usage: alertbook [-h] [-r DIR] [-o DIR] book [book ...]

positional arguments:
  book

optional arguments:
  -h, --help               show this help message and exit
  -r DIR, --rules-dir DIR  base directory of rules (default: './rules')
  -o DIR, --out-dir DIR    directory for compiled rules (default: './out')
```

### Example

Let's use the following project structure

```
alertbook_proj
├── foo_cluster.yml
└── rules
    ├── DiskFailure
    └── DiskUsageHigh
```

where,
```
$ cat foo_cluster.yml 
---
name: Prometheus Alert Rules for foo cluster
rules:
  - file: DiskFailure
    conds:
      - prio: low
        hours: [8,16]
      - prio: high
        hours: 4
  - file: DiskUsageHigh
    conds:
      - threshold: 85
        prio: high
```
```
$ cat rules/DiskFailure 
ALERT DiskWillFillIn{%hours}Hours
    IF predict_linear(node_filesystem_free[1h], ${hours}*3600) < 0
    FOR 5m
    LABELS { severity="${prio}" }
```
```
$ cat rules/DiskUsageHigh 
ALERT DiskUsageOver${threshold}Percent
    IF node_filesystem_avail / node_filesystem_size < (100 - ${threshold}) / 100
    FOR 5m
    LABELS { severity = "${prio}" }
    ANNOTATIONS {
        description = "{{ $labels.instance }} disk usage has over {$threshold}%."
    }
```

if we examine the `rules` section of the `rulebook` we can see that we're using
2 rules.

The 2nd rule, `DiskUsageHigh`, is fairly straightforward, we are just
populating the values of the variables in the rule file, one for disk
percentage, and one for alert priority.

The 1st rule however has a it more going on:
```
- file: DiskFailure
    conds:
      - prio: low
        hours: [8,16]
      - prio: high
        hours: 4
```
It's second condition is just like the `DiskUsageHigh` rule's form, but the
first condition has an array.  Again, when `alertbook` encounters an array in
one or more of a conditions variables, it constructs the Cartesian product of
them and essentially generates one condition for each.  With that in mind, we
could interpret

```
conds:
  - foo: [bar, baz]
    floop: [doop,  boop]
```
as being equivalent to  
```
conds:
  - foo: bar
    floop: doop
  - foo: bar
    floop: boop
  - foo: baz
    floop: doop
  - foo: baz
    floop: boop
```

When we run

```
alertbook foo_cluster
```

the following file is generated and output to `foo_cluster.rules` in the
`./out` directory

```
##########################################
# Prometheus Alert Rules for foo cluster #
##########################################

## DiskFailure

ALERT DiskWillFillIn{%hours}Hours
    IF predict_linear(node_filesystem_free[1h], 8*3600) < 0
    FOR 5m
    LABELS { severity="low" }

ALERT DiskWillFillIn{%hours}Hours
    IF predict_linear(node_filesystem_free[1h], 16*3600) < 0
    FOR 5m
    LABELS { severity="low" }

ALERT DiskWillFillIn{%hours}Hours
    IF predict_linear(node_filesystem_free[1h], 4*3600) < 0
    FOR 5m
    LABELS { severity="high" }


## DiskUsageHigh

ALERT DiskUsageOver70Percent
    IF node_filesystem_avail / node_filesystem_size < (100 - 70) / 100
    FOR 5m
    LABELS { severity = "low" }
    ANNOTATIONS {
        description = "{{ $labels.instance }} disk usage has over {$threshold}%."
    }

ALERT DiskUsageOver85Percent
    IF node_filesystem_avail / node_filesystem_size < (100 - 85) / 100
    FOR 5m
    LABELS { severity = "high" }
    ANNOTATIONS {
        description = "{{ $labels.instance }} disk usage has over {$threshold}%."
    }
```
