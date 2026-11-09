

[id=policy, 
	 policy.method: !egm(block=egm, grid=A_grid),
    (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] 
	 | policy.evaluate.method:  !Linear(grid=M_grid, orders) {
	     c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])     :: [id=optimality]
}

the problem iss suppose wehave the above, then do can we tell taht 	 policy.evaluate.method:  !Linear ios not part of the codimain of the signa there that prceeds it?

in the methods.bl

[id=policy, ++ policy.methods: .....]{...egmblock :: [id = egm_block]}

[id=policy, | ++ policy.evaluate.methods:.....]

on the the fiorsrt, ++ says add it to the first thing after policty ie wppend the first entry, and the |++ satys ad a new entry. this doesnt look clean howver?