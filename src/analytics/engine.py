from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..models.models import Organization, User, Badge, Course, Enrollment

class AnalyticsEngine:
    def __init__(self, db: Session):
        self.db = db
        
    def _create_multi_visualization(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], query_type: str) -> Dict[str, Any]:
        """Creates multiple visualizations for the data
        
        Args:
            data: Either a list of dictionaries or a single dictionary with the data
            query_type: Type of visualization to create (enrollment or timeline)
        """
        figs = {}
        df = pd.DataFrame(data if isinstance(data, list) else [data])
        
        if query_type == "enrollment":
            # Primary visualization (bar chart)
            figs["bar"] = px.bar(df, x='badge', y=['total_enrollments', 'completed'],
                                title='Badge Enrollments and Completions',
                                barmode='group')
            
            # Radar chart for completion rates
            figs["radar"] = go.Figure()
            figs["radar"].add_trace(go.Scatterpolar(
                r=df['completion_rate'],
                theta=df['badge'],
                fill='toself',
                name='Completion Rate'
            ))
            figs["radar"].update_layout(title='Completion Rates by Badge')
            
            # Funnel chart for enrollment stages
            stages = ['total_enrollments', 'completed']
            figs["funnel"] = go.Figure(go.Funnel(
                y=stages,
                x=df[stages].sum(),
                textinfo="value+percent initial"
            ))
            figs["funnel"].update_layout(title='Enrollment Pipeline')
            
        elif query_type == "timeline":
            # Line chart
            figs["line"] = px.line(df, x='month', y='enrollments', 
                                 color='organization',
                                 title='Enrollment Timeline')
            
            # Area chart
            figs["area"] = px.area(df, x='month', y='enrollments',
                                 color='organization',
                                 title='Cumulative Enrollments')
            
            # Box plot by month
            figs["box"] = px.box(df, x='month', y='enrollments',
                               title='Enrollment Distribution by Month')
            
        return {name: fig.to_json() for name, fig in figs.items()}

    def get_badge_enrollments(self, badge_name: str = None) -> Dict[str, Any]:
        """Get enrollment statistics for a specific badge or all badges with multiple visualizations"""
        query = self.db.query(
            Badge.name,
            func.count(Enrollment.id).label('total_enrollments'),
            func.count(Enrollment.completion_date).label('completed'),
            func.avg(func.julianday(Enrollment.completion_date) - 
                    func.julianday(Enrollment.enrollment_date)).label('avg_completion_time')
        ).join(Enrollment).group_by(Badge.name)
        
        if badge_name:
            query = query.filter(Badge.name == badge_name)
        
        results = query.all()
        
        data = [{
            'badge': r[0],
            'total_enrollments': r[1],
            'completed': r[2],
            'completion_rate': round(r[2] / r[1] * 100 if r[1] > 0 else 0, 2),
            'avg_completion_time': round(r[3] if r[3] is not None else 0, 2)
        } for r in results]
        
        # Create multiple visualizations
        visualizations = self._create_multi_visualization(data, "enrollment")
        
        # Add bubble chart for multi-dimensional view
        df = pd.DataFrame(data)
        bubble_fig = px.scatter(df, 
            x='total_enrollments',
            y='completion_rate',
            size='avg_completion_time',
            color='badge',
            title='Multi-dimensional Badge Analysis',
            labels={
                'total_enrollments': 'Total Enrollments',
                'completion_rate': 'Completion Rate (%)',
                'avg_completion_time': 'Avg. Completion Time (days)'
            }
        )
        visualizations["bubble"] = bubble_fig.to_json()
        
        return {
            'data': data,
            'visualizations': visualizations
        }

    def get_organization_trends(self, org_name: str = None) -> Dict[str, Any]:
        """Get enrollment trends for an organization or all organizations"""
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        query = self.db.query(
            Organization.name,
            func.strftime('%Y-%m', Enrollment.enrollment_date).label('month'),
            func.count(Enrollment.id).label('enrollments')
        ).select_from(Organization)\
         .join(User, User.organization_id == Organization.id)\
         .join(Enrollment, Enrollment.user_id == User.id)\
         .filter(Enrollment.enrollment_date >= six_months_ago)\
         .group_by(Organization.name, func.strftime('%Y-%m', Enrollment.enrollment_date))
        
        if org_name:
            query = query.filter(Organization.name == org_name)
            
        results = query.all()
        
        # Convert to pandas for easier processing
        data = [{
            'organization': r[0],
            'month': r[1],
            'enrollments': r[2]
        } for r in results]
        
        # Create visualizations using the helper method
        visualizations = self._create_multi_visualization(data, "timeline")
        
        # For trend queries, the line chart is the most appropriate visualization
        return {
            'data': data,
            'visualization': visualizations.get('line'),
            'visualizations': visualizations  # Keep all visualizations for potential future use
        }

    def get_completion_metrics(self) -> Dict[str, Any]:
        """Get detailed completion metrics with multiple visualizations"""
        results = self.db.query(
            Badge.name,
            Organization.name,
            func.avg(
                func.julianday(Enrollment.completion_date) - 
                func.julianday(Enrollment.enrollment_date)
            ).label('avg_days_to_complete'),
            func.count(Enrollment.id).label('total_enrollments'),
            func.count(Enrollment.completion_date).label('completions'),
            func.min(
                func.julianday(Enrollment.completion_date) - 
                func.julianday(Enrollment.enrollment_date)
            ).label('min_days'),
            func.max(
                func.julianday(Enrollment.completion_date) - 
                func.julianday(Enrollment.enrollment_date)
            ).label('max_days')
        ).join(Badge).join(User).join(Organization)\
         .group_by(Badge.name, Organization.name).all()
        
        data = [{
            'badge': r[0],
            'organization': r[1],
            'avg_days_to_complete': round(r[2] if r[2] is not None else 0, 2),
            'total_enrollments': r[3],
            'completions': r[4],
            'completion_rate': round(r[4] / r[3] * 100 if r[3] > 0 else 0, 2),
            'min_days': round(r[5] if r[5] is not None else 0, 2),
            'max_days': round(r[6] if r[6] is not None else 0, 2)
        } for r in results]
        
        df = pd.DataFrame(data)
        visualizations = {}
        
        # 1. Heatmap for completion rates
        pivot_df = df.pivot(index='organization', columns='badge', values='completion_rate')
        heatmap = px.imshow(pivot_df,
                          title='Completion Rates by Organization and Badge (%)',
                          labels=dict(x='Badge', y='Organization', color='Completion Rate %'))
        visualizations["heatmap"] = heatmap.to_json()
        
        # 2. Box plot for completion times
        box_data = []
        for _, row in df.iterrows():
            box_data.extend([{
                'badge': row['badge'],
                'org': row['organization'],
                'days': days
            } for days in np.linspace(row['min_days'], row['max_days'], 
                                    num=row['completions'])])
        
        box_df = pd.DataFrame(box_data)
        box_fig = px.box(box_df, x='badge', y='days', color='org',
                        title='Completion Time Distribution by Badge and Organization')
        visualizations["box_plot"] = box_fig.to_json()
        
        # 3. Sunburst chart for hierarchical view
        sunburst_fig = px.sunburst(df, 
                                  path=['organization', 'badge'],
                                  values='total_enrollments',
                                  color='completion_rate',
                                  title='Hierarchical View of Enrollments and Completion Rates')
        visualizations["sunburst"] = sunburst_fig.to_json()
        
        # 4. Parallel categories for multi-dimensional analysis
        parallel_fig = px.parallel_categories(df,
                                            dimensions=['organization', 'badge'],
                                            color='completion_rate',
                                            title='Multi-dimensional Completion Analysis')
        visualizations["parallel"] = parallel_fig.to_json()
        
        # 5. Scatter matrix for correlations
        scatter_matrix = px.scatter_matrix(df,
                                         dimensions=['total_enrollments', 'completions', 
                                                   'avg_days_to_complete', 'completion_rate'],
                                         title='Correlation Matrix of Completion Metrics')
        visualizations["scatter_matrix"] = scatter_matrix.to_json()
        
        return {
            'data': data,
            'visualizations': visualizations
        }

    def get_learning_paths(self) -> Dict[str, Any]:
        """Analyze common learning paths and badge combinations with multiple visualizations"""
        # Get users with multiple badges and their enrollment dates
        user_badges = self.db.query(
            User.id,
            User.name,
            Organization.name.label('organization'),
            func.group_concat(Badge.name).label('badge_path'),
            func.group_concat(Enrollment.enrollment_date).label('enrollment_dates')
        ).join(Enrollment).join(Badge).join(Organization)\
         .group_by(User.id, User.name, Organization.name)\
         .having(func.count(Badge.id) > 1).all()
        
        paths = {}
        path_details = []
        
        for user in user_badges:
            badge_list = list(zip(user[3].split(','), user[4].split(',')))
            # Sort by enrollment date
            badge_list.sort(key=lambda x: x[1])
            badges = [b[0] for b in badge_list]
            path_key = ' → '.join(badges)
            paths[path_key] = paths.get(path_key, 0) + 1
            
            # Collect detailed path information
            path_details.append({
                'user_id': user[0],
                'user_name': user[1],
                'organization': user[2],
                'path': badges,
                'dates': [b[1] for b in badge_list]
            })
        
        visualizations = {}
        
        # 1. Enhanced Sankey diagram
        path_data = []
        for path, count in paths.items():
            badges = path.split(' → ')
            for i in range(len(badges) - 1):
                path_data.append({
                    'source': badges[i],
                    'target': badges[i + 1],
                    'value': count
                })
        
        df = pd.DataFrame(path_data)
        all_nodes = pd.concat([df['source'], df['target']]).unique()
        node_indices = {node: idx for idx, node in enumerate(all_nodes)}
        
        sankey_fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color="blue"  # Add color for better visibility
            ),
            link=dict(
                source=[node_indices[row['source']] for _, row in df.iterrows()],
                target=[node_indices[row['target']] for _, row in df.iterrows()],
                value=df['value'],
                color="rgba(0,0,255,0.2)"  # Semi-transparent links
            )
        )])
        sankey_fig.update_layout(title="Learning Path Flows")
        visualizations["sankey"] = sankey_fig.to_json()
        
        # 2. Network graph
        network_fig = go.Figure()
        
        # Add nodes
        for node in all_nodes:
            network_fig.add_trace(go.Scatter(
                x=[0],
                y=[0],
                mode='markers+text',
                name=node,
                text=[node],
                textposition="bottom center"
            ))
        
        network_fig.update_layout(
            title="Badge Relationship Network",
            showlegend=True,
            hovermode='closest'
        )
        visualizations["network"] = network_fig.to_json()
        
        # 3. Timeline visualization
        timeline_data = []
        for detail in path_details:
            for badge, date in zip(detail['path'], detail['dates']):
                timeline_data.append({
                    'organization': detail['organization'],
                    'badge': badge,
                    'date': date,
                    'user': detail['user_name']
                })
        
        timeline_df = pd.DataFrame(timeline_data)
        timeline_fig = px.timeline(timeline_df,
                                 x_start='date',
                                 y='user',
                                 color='badge',
                                 title="Individual Learning Paths Timeline")
        visualizations["timeline"] = timeline_fig.to_json()
        
        # 4. Chord diagram for badge relationships
        matrix = np.zeros((len(all_nodes), len(all_nodes)))
        for _, row in df.iterrows():
            i = list(all_nodes).index(row['source'])
            j = list(all_nodes).index(row['target'])
            matrix[i][j] = row['value']
        
        chord_fig = go.Figure(data=[go.Heatmap(
            z=matrix,
            x=all_nodes,
            y=all_nodes,
            colorscale='Blues'
        )])
        chord_fig.update_layout(title="Badge Relationship Matrix")
        visualizations["chord"] = chord_fig.to_json()
        
        # 5. Tree map of popular paths
        treemap_fig = px.treemap(
            path_data,
            path=[px.Constant("All Paths"), 'source', 'target'],
            values='value',
            title="Popular Learning Path Combinations"
        )
        visualizations["treemap"] = treemap_fig.to_json()
        
        return {
            'data': {
                'paths': paths,
                'path_details': path_details
            },
            'visualizations': visualizations
        }
