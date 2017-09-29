from sympy.abc import t, n, x, y, p, q, f, s, r, mu, omega
from sympy import diff, solve, simplify

p_LB = t * q * p * (1 - 2**(-mu))
p_sup = (1 - f)**r * (r * (r - 1) / 2) * p_LB**2 * (1 - p_LB)**(r - 2)
p_SB = (n - t) * q * p * 2**(-mu)

exp_adv_chain = x * t * q * p * 2**(-mu)
exp_hon_chain = s * (n - t) * q * p * 2**(-mu) * (1 - p_sup)

# dp_sup = diff(p_sup, r)
# optimal_r = solve(simplify(dp_sup), r)

subs = [
    (s, x + r * y),
    (x, (1 - p_SB) * omega),
    (y, p_SB * omega),
    (f, 1 - (1 - p)**(q * (n - t))),
    (p, 0.00001),
    (q, 1),
    (n, 1000),
    (t, 489),
    (mu, 25),
    (r, 200),
    # (omega, 1000000000000),
]

exp_hon_chain *= (1 + r * p * q * (n - t) * 2**(-mu))

# print(optimal_r[0].subs(subs))

# subs = [(r, optimal_r[0].subs(subs))] + subs

# print('optimal r')
# print(optimal_r[0].subs(subs))

# print(p_sup.subs(subs))

# print(f.subs(subs))
# ratio = exp_adv_chain / exp_hon_chain

print(
    'Adversary chain length: %s\n Honest chain length: %s'
    % (exp_adv_chain.subs(subs), exp_hon_chain.subs(subs))
)
