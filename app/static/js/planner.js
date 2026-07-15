/**
 * EduPilot – Study Planner JavaScript
 */

async function generatePlan() {
  const btn = document.getElementById('generateBtn');
  const loadingState = document.getElementById('loadingState');
  const planDisplay = document.getElementById('planDisplay');

  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Generating...';
  if (loadingState) loadingState.style.display = 'block';
  if (planDisplay) planDisplay.style.opacity = '0.5';

  try {
    const resp = await fetch('/planner/generate', { method: 'POST' });
    const data = await resp.json();

    if (data.success) {
      // Reload page to show new plan
      window.location.reload();
    }
  } catch (e) {
    alert('Error generating plan. Please try again.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-cpu"></i> Generate AI Plan';
    if (loadingState) loadingState.style.display = 'none';
    if (planDisplay) planDisplay.style.opacity = '1';
  }
}
