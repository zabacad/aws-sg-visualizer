# AWS security group visualizer

Create a Dot graph of AWS security groups (rectangular nodes), their inbound
rules (edges), plus allowed CIDR blocks (oval nodes).

Example usage:

```
./sg-graph.py > security-groups.dot
neato -n -Tsvg -o security-groups.svg security-groups.dot
```

You'll need AWS credentials [anywhere Boto can find them][boto-creds]

## Requirements

- [Python 3][py]
- [Boto 3][boto3]
- [Graphviz Python module][py-graphviz]
- [Graphviz][graphviz] — To render the Dot file

## Installation

Using Virtualenv is recommended.

Make sure pip is for Python 3. (Indicated at the end of the version.)

```
pip --version
```

Manually:

```
pip install boto3 graphviz
```

Or, to install tested versions of dependencies:

```
pip install -r requirements.txt
```

## Shortcomings

- A single VPC is assumed.
- A single AWS account is assumed. No VPC peering.
- Security groups with the tag `created_by` set to `puppet` are colored blue
and grouped in a separate `managed` subgraph. The tag value not case sensitive.
- Only ingress rules are considered.
- The final diagram is at the mercy of the whims of Graphviz. More complex
  diagrams and small changes in Graphviz version are likely to mess things up.

[boto-creds]: https://boto3.readthedocs.io/en/latest/guide/configuration.html
[py]: https://www.python.org/
[boto3]: https://pypi.python.org/pypi/boto3
[py-graphviz]: https://pypi.python.org/pypi/graphviz
[graphviz]: http://www.graphviz.org/
