import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from networkx.algorithms import community as nx_comm
import warnings
import datacleaning
from networkx.algorithms.community import modularity

warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

EDGE_THRESHOLD = 3
LOUVAIN_SEED = 42

df_clean = datacleaning.df_clean.copy()

df_clean = df_clean.rename(columns={
    'birthCountryLabel': 'birth',
    'mainResearchCountry': 'research'
})

df_stayed = df_clean[df_clean['birth'] == df_clean['research']].copy()
stayed_counts = df_stayed['birth'].value_counts().to_dict()

df_migration = df_clean[df_clean['birth'] != df_clean['research']].copy()

edge_df_overall = (
    df_migration
    .groupby(['birth', 'research'])
    .size()
    .reset_index(name='migrants_count')
)
edge_df_overall['migrants_count'] = edge_df_overall['migrants_count'].astype(int)

G_overall = nx.DiGraph()
for _, row in edge_df_overall.iterrows():
    G_overall.add_edge(row['birth'], row['research'], weight=row['migrants_count'])

G_undirected = G_overall.to_undirected()

nodes_overall = sorted(G_overall.nodes())
in_strength_overall = dict(G_overall.in_degree(weight='weight'))
out_strength_overall = dict(G_overall.out_degree(weight='weight'))

nodes_df_overall = pd.DataFrame({
    'country': nodes_overall,
    'in_strength_migrants': [in_strength_overall.get(c, 0) for c in nodes_overall],
    'out_strength_migrants': [out_strength_overall.get(c, 0) for c in nodes_overall],
})
nodes_df_overall['net_flow'] = (
    nodes_df_overall['in_strength_migrants'] -
    nodes_df_overall['out_strength_migrants']
)

nodes_df_overall['stayed'] = (
    nodes_df_overall['country']
    .map(stayed_counts)
    .fillna(0)
    .astype(int)
)

nodes_df_overall['total_stock'] = (
    nodes_df_overall['stayed'] +
    nodes_df_overall['in_strength_migrants']
)

stock_rank = (
    nodes_df_overall
    .sort_values('total_stock', ascending=False)
    .head(10)
    .reset_index(drop=True)
)

communities = nx_comm.louvain_communities(
    G_undirected,
    weight='weight',
    seed=LOUVAIN_SEED
)

community_mapping = {}
for i, comm in enumerate(communities):
    for node in comm:
        community_mapping[node] = i

nodes_df_overall['community_id'] = nodes_df_overall['country'].map(community_mapping)

Q = modularity(G_undirected, communities, weight='weight')
print("Modularity Q:", Q)

print("Louvain communities:")
for i, comm in enumerate(communities):
    print(f"Community {i} (n = {len(comm)}):")
    print(sorted(list(comm)))
    print()

top_10_net_in = (
    nodes_df_overall
    .sort_values('net_flow', ascending=False)
    .head(10)
    .reset_index(drop=True)
)

plt.figure(figsize=(8, 5))
plt.barh(
    top_10_net_in['country'],
    top_10_net_in['net_flow'],
    color=['green' if x > 0 else 'red' for x in top_10_net_in['net_flow']],
    alpha=0.8
)
plt.xlabel('Net Flow (Inflow - Outflow)')
plt.title('Top 10 Countries: Talent Net Inflow')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('plot_top10_net_inflow_countries.png', dpi=300, bbox_inches='tight')
plt.show()

top_10_net_out = (
    nodes_df_overall
    .sort_values('net_flow', ascending=True)
    .head(10)
    .reset_index(drop=True)
)

plt.figure(figsize=(8, 5))
plt.barh(
    top_10_net_out['country'],
    top_10_net_out['net_flow'],
    color=['red' if x < 0 else 'green' for x in top_10_net_out['net_flow']],
    alpha=0.8
)
plt.xlabel('Net Flow (Inflow - Outflow)')
plt.title('Top 10 Countries: Talent Net Outflow')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('plot_top10_net_outflow_countries.png', dpi=300, bbox_inches='tight')
plt.show()

top_10_routes = (
    edge_df_overall
    .sort_values('migrants_count', ascending=False)
    .head(10)
    .reset_index(drop=True)
)

plt.figure(figsize=(10, 6))
routes = top_10_routes.apply(lambda row: f"{row['birth']} → {row['research']}", axis=1)

plt.barh(routes, top_10_routes['migrants_count'], color='skyblue')
plt.xlabel('Number of Laureates')
plt.title('Top 10 Nobel Laureate Mobility Routes (Birth → Research)')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('top10_mobility_routes.png', dpi=300)
plt.show()

G_filtered = nx.DiGraph()
for _, row in edge_df_overall[edge_df_overall['migrants_count'] >= EDGE_THRESHOLD].iterrows():
    G_filtered.add_edge(row['birth'], row['research'], weight=row['migrants_count'])

pos = nx.spring_layout(
    G_filtered,
    k=1,
    iterations=200,
    weight='weight',
    seed=42
)

edges = list(G_filtered.edges())
weights = [G_filtered[u][v]['weight'] for u, v in edges]

fig2, ax2 = plt.subplots(figsize=(16, 12))

node_colors_flow = []
node_sizes = []
for node in G_filtered.nodes():
    net = nodes_df_overall.loc[nodes_df_overall['country'] == node, 'net_flow'].values
    if len(net) > 0:
        node_colors_flow.append(net[0])
    else:
        node_colors_flow.append(0)
    node_sizes.append(500 + 100 * G_filtered.degree(node, weight='weight'))

nx.draw_networkx_nodes(
    G_filtered,
    pos,
    node_size=node_sizes,
    node_color=node_colors_flow,
    cmap='RdYlGn',
    alpha=0.8,
    edgecolors='black',
    linewidths=2,
    ax=ax2
)

nx.draw_networkx_labels(
    G_filtered,
    pos,
    font_size=10,
    font_weight='bold',
    ax=ax2
)

nx.draw_networkx_edges(
    G_filtered,
    pos,
    edgelist=edges,
    width=[w / 2 for w in weights],
    alpha=0.3,
    edge_color='darkblue',
    arrows=True,
    arrowsize=15,
    arrowstyle='->',
    connectionstyle='arc3,rad=0.1',
    ax=ax2
)

ax2.set_title(
    'Nobel Prize Research Mobility Network\n'
    'Node Color: Green = Net Inflow, Red = Net Outflow\n'
    'Node Size: Total Flow Volume',
    fontsize=14,
    fontweight='bold',
    pad=20
)
ax2.axis('off')

sm = plt.cm.ScalarMappable(
    cmap='RdYlGn',
    norm=plt.Normalize(vmin=min(node_colors_flow), vmax=max(node_colors_flow))
)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax2, orientation='horizontal', pad=0.05, aspect=40)
cbar.set_label('Net Flow (Inflow - Outflow)', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('nobel_migration_network_circular.png', dpi=300, bbox_inches='tight')
plt.show()

plt.figure(figsize=(10, 8))

x = nodes_df_overall['in_strength_migrants']
y = nodes_df_overall['stayed']

sc = plt.scatter(
    x,
    y,
    c=nodes_df_overall['net_flow'],
    cmap='RdYlGn',
    s=200,
    alpha=0.8,
    edgecolors='black'
)

plt.xscale('log')
plt.yscale('log')

plt.xlabel("Inflow (log scale)", fontsize=12)
plt.ylabel("Stayed (log scale)", fontsize=12)
plt.title("Scientific Talent Map (Log-Scaled)", fontsize=14)

label_countries = (
    nodes_df_overall
    .sort_values('total_stock', ascending=False)
    .head(15)['country']
    .tolist()
)

for _, row in nodes_df_overall.iterrows():
    if row['country'] in label_countries:
        plt.text(
            row['in_strength_migrants'] * 1.05,
            row['stayed'] * 1.05,
            row['country'],
            fontsize=9
        )

cbar = plt.colorbar(sc, label="Net Flow (Inflow - Outflow)")
plt.tight_layout()
plt.savefig('plot_talent_map_no_quadrants.png', dpi=300, bbox_inches='tight')
plt.show()

total_laureates = df_clean['laureateName'].nunique()
total_countries = nodes_df_overall['country'].nunique()
total_migrations = len(df_migration)

with open("summary_report.txt", "w", encoding="utf-8") as f:
    f.write("Nobel Prize Research Mobility – Summary Report\n")
    f.write("=============================================\n\n")
    f.write(f"Total unique laureates (after cleaning): {total_laureates}\n")
    f.write(f"Total countries in network: {total_countries}\n")
    f.write(f"Total cross-border migration records (birth != research): {total_migrations}\n\n")

    f.write("Top 10 Countries by Talent Net Inflow (Inflow - Outflow)\n")
    f.write("--------------------------------------------------------\n")
    for _, row in top_10_net_in.iterrows():
        f.write(f"{row['country']}: net_flow = {row['net_flow']}\n")
    f.write("\n")

    f.write("Top 10 Migration Routes (Birth → Research)\n")
    f.write("-----------------------------------------\n")
    for _, row in top_10_routes.iterrows():
        f.write(f"{row['birth']} → {row['research']}: {row['migrants_count']} laureates\n")
    f.write("\n")

    f.write("Top 10 Countries by Talent Stock (Stayed + Inflow)\n")
    f.write("--------------------------------------------------\n")
    for _, row in stock_rank.iterrows():
        f.write(
            f"{row['country']}: total_stock = {row['total_stock']}, "
            f"stayed = {row['stayed']}, inflow = {row['in_strength_migrants']}\n"
        )
    f.write("\n")

    f.write("Community Structure (Louvain)\n")
    f.write("--------------------------------\n")
    f.write(f"Modularity Q = {Q:.3f}\n\n")

    for i, comm in enumerate(communities):
        f.write(f"Community {i} (n = {len(comm)}):\n")
        f.write(", ".join(sorted(list(comm))) + "\n\n")

print("summary_report.txt generated.")
