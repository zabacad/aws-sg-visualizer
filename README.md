# AWS security group visualizer

Create a Dot graph of AWS security groups (rectangular nodes), their inbound
rules (edges), plus allowed CIDR blocks (oval nodes).

Example usage:

```
./sg-graph.py > security-groups.dot
neato -n -Tsvg -o security-groups.svg security-groups.dot
```

You'll need AWS credentials [anywhere Boto can find them](https://boto3.readthedocs.io/en/latest/guide/configuration.html).

## Requirements

* [Python 3](https://www.python.org/)
* [Boto 3](https://pypi.python.org/pypi/boto3)
* [Graphviz Python module](https://pypi.python.org/pypi/graphviz)
* [Graphviz](http://www.graphviz.org/) — To render the Dot file

To install Python modules:

```
pip install boto3 graphviz
```

Or:

```
pip install -r requirements.txt
```

## Shortcomings

- A single VPC is assumed.
- A single AWS account is assumed. No VPC peering.
- Security groups with the tag `created_by` set to `puppet` are colored blue
and grouped in a separate `managed` subgraph. The tag value not case sensitive.
- Only ingress rules are considered.

## FAQ

*How are you?*

I'm fine. Thanks.
