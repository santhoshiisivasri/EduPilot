/**
 * EduPilot – Charts JavaScript
 * All Chart.js analytics charts
 */

document.addEventListener('DOMContentLoaded', () => {
  loadAnalyticsData();
});

const isDark = () => document.documentElement.getAttribute('data-theme') === 'dark';

function chartDefaults() {
  const dark = isDark();
  return {
    gridColor: dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)',
    textColor: dark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)',
    tooltipBg: dark ? '#1a1a3e' : '#ffffff',
    tooltipText: dark ? '#e8eaf6' : '#1a1a2e',
  };
}

async function loadAnalyticsData() {
  try {
    const resp = await fetch('/analytics/data');
    const data = await resp.json();

    // Update stat cards
    animateStatCard('totalMessages', data.total_messages || 0);
    animateStatCard('totalMilestones', data.total_milestones_done || 0);
    animateStatCard('totalAssessments', data.total_assessments || 0);
    const avgEl = document.getElementById('avgScore');
    if (avgEl) avgEl.textContent = (data.avg_assessment_score || 0) + '%';

    const readiness = document.getElementById('readinessDisplay');
    if (readiness) {
      let count = 0;
      const target = data.readiness_score || 0;
      const interval = setInterval(() => {
        count += Math.ceil(target / 30);
        if (count >= target) { count = target; clearInterval(interval); }
        readiness.textContent = count + '%';
      }, 50);
    }

    // Render charts
    renderWeeklyChart(data.weekly_hours || []);
    renderDayChart(data.day_activity || [0,0,0,0,0,0,0]);
    renderAssessmentChart(data.assessments || []);
    renderMilestoneChart(data.milestones_by_level || {});

  } catch (e) {
    console.error('Analytics data error:', e);
  }
}

function animateStatCard(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let count = 0;
  const step = Math.ceil(target / 40);
  const timer = setInterval(() => {
    count += step;
    if (count >= target) { count = target; clearInterval(timer); }
    el.textContent = count;
  }, 40);
}

function renderWeeklyChart(weeklyData) {
  const canvas = document.getElementById('weeklyChart');
  if (!canvas) return;
  const { gridColor, textColor } = chartDefaults();

  new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: weeklyData.map(w => w.week),
      datasets: [{
        label: 'Study Hours',
        data: weeklyData.map(w => w.hours),
        backgroundColor: 'rgba(108,99,255,0.6)',
        borderColor: '#6C63FF',
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      }, {
        label: 'Messages',
        data: weeklyData.map(w => w.messages * 0.1),
        backgroundColor: 'rgba(255,107,157,0.4)',
        borderColor: '#FF6B9D',
        borderWidth: 2,
        borderRadius: 8,
        type: 'line',
        fill: false,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#FF6B9D',
        yAxisID: 'y',
      }]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: textColor, font: { size: 12 } } },
        tooltip: {
          backgroundColor: '#1a1a3e',
          titleColor: '#e8eaf6',
          bodyColor: 'rgba(255,255,255,0.7)',
          borderColor: 'rgba(108,99,255,0.3)',
          borderWidth: 1,
        }
      },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: textColor } },
        y: { grid: { color: gridColor }, ticks: { color: textColor }, beginAtZero: true }
      }
    }
  });
}

function renderDayChart(dayData) {
  const canvas = document.getElementById('dayChart');
  if (!canvas) return;
  const { gridColor, textColor } = chartDefaults();

  new Chart(canvas.getContext('2d'), {
    type: 'radar',
    data: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [{
        label: 'Activity',
        data: dayData,
        backgroundColor: 'rgba(108,99,255,0.2)',
        borderColor: '#6C63FF',
        borderWidth: 2,
        pointBackgroundColor: '#6C63FF',
        pointRadius: 4,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        r: {
          grid: { color: gridColor },
          ticks: { display: false },
          pointLabels: { color: textColor, font: { size: 12, weight: '600' } }
        }
      }
    }
  });
}

function renderAssessmentChart(assessments) {
  const canvas = document.getElementById('assessmentChart');
  if (!canvas || !assessments.length) return;
  const { gridColor, textColor } = chartDefaults();

  new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: assessments.map(a => a.domain + ' (' + a.date + ')'),
      datasets: [{
        label: 'Score',
        data: assessments.map(a => a.score),
        borderColor: '#FFB347',
        backgroundColor: 'rgba(255,179,71,0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#FFB347',
        pointRadius: 6,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: textColor } },
        y: { grid: { color: gridColor }, ticks: { color: textColor }, min: 0, max: 100 }
      }
    }
  });
}

function renderMilestoneChart(byLevel) {
  const canvas = document.getElementById('milestoneChart');
  if (!canvas) return;

  const levels = ['beginner', 'intermediate', 'advanced'];
  const colors = ['rgba(46,213,115,0.8)', 'rgba(108,99,255,0.8)', 'rgba(255,107,157,0.8)'];

  new Chart(canvas.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: levels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
      datasets: [{
        data: levels.map(l => (byLevel[l] || {}).done || 0),
        backgroundColor: colors,
        borderColor: isDark() ? '#0a0a1a' : '#ffffff',
        borderWidth: 3,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: isDark() ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)', padding: 16, font: { size: 12 } }
        }
      }
    }
  });
}
