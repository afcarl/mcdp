## Coproducts (alternatives)

The *coproduct* construct allows to describe the idea of 
"alternatives". The name comes from [the category-theoretical concept
of coproduct][cat-coproduct].

[cat-coproduct]: https://en.wikipedia.org/wiki/Coproduct

As an example, let us consider how to model the choice
between different battery technologies.

Let us consider the model of a battery in which we take 
the functionality to be the capacity 
and the resources to be the mass [g] and the cost [$].


<pre class='mcdp' id='Battery' style='display:none'>
mcdp {
	provides capacity [J]
	requires mass [g]
	requires cost [$]
	
	specific_energy = 150 Wh/kg
    specific_cost = 2.50 Wh/$

	required mass >= provided capacity / specific_energy
	required cost >= provided capacity / specific_cost
}
</pre>

<pre class='ndp_graph_templatized_labeled'>`Battery</pre>


Consider two different battery technologies, 
characterized by their specific energy (Joules per gram)
and specific cost (USD per gram).

Specifically, consider [Nickel-Hidrogen batteries][NiH2]
and [Lithium-Polymer][LiPo] batteries. 
On technology is cheaper but leads to heavier batteries
and viceversa. Because of this fact, there might be designs
in which we prefer either.

[NiH2]: https://en.wikipedia.org/wiki/Nickel%E2%80%93hydrogen_battery
[Lipo]: https://en.wikipedia.org/wiki/Lithium_polymer_battery

First we model the two battery technologies separately
as two MCDP using the same interface (same resources and same functionality).

<table>
<tr>
<td>
<pre class='mcdp' id='battery_LiPo' label='Battery_LiPo.mcdp'>
mcdp {
	provides capacity [J]
	requires mass [g]
	requires cost [$]
	
	specific_energy = 150 Wh/kg
    specific_cost = 2.50 Wh/$

	required mass >= provided capacity / specific_energy
	required cost >= provided capacity / specific_cost
}
</pre>
</td>
<td>
<pre class='mcdp' id='Battery_NiH2' label='Battery_NiH2.mcdp'>
mcdp {
	provides capacity [J]
	requires mass [g]
	requires cost [$]
	
	specific_energy = 45 Wh/kg
    specific_cost = 10.50 Wh/$ 

	required mass >= provided capacity / specific_energy
	required cost >= provided capacity / specific_cost
}
</pre>
</td>
</tr>
	<tr>
		<td>
			<pre class='ndp_graph_templatized_labeled'>`Battery_LiPo</pre>
		</td>
		<td>
			<pre class='ndp_graph_templatized_labeled'>`Battery_NiH2</pre>
		</td>
	</tr>
</table>

Then we can define the **coproduct** of the two using
the keyword <code><span class="CoproductWithNamesChooseKeyword">choose</span></code>.
Graphically, the choice is indicated through dashed lines.

<table>
<tr>
<td valign="top">
<pre class='mcdp' id='Batteries' label='Batteries.mcdp'>
choose(
	NiH2: `Battery_LiPo,
	LiPo: `Battery_NiH2
)
</pre>
</td>
<td valign="top">
<pre class='ndp_graph_enclosed'>`Batteries</pre>
</td>
</tr>
</table>





