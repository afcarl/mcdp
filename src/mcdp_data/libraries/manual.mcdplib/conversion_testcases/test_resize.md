
<pre class='mcdp' id='compact_example'>
    mcdp {
      a = instance template mcdp {
          provides f [Nat]
          requires r1 [Nat]
          requires r2 [Nat]
      }
      b = instance template mcdp {
          provides f1 [Nat]
          provides f2 [Nat]
          requires r [Nat]
      }
      a.r1 ≼ b.f1
      a.r2 ≼ b.f2
    }
</pre>

<render class='ndp_graph_expand'>`compact_example</render>