(function () {
  'use strict';

  var els = {
	nodesSummary: document.getElementById('nodes-summary'),
	nodesGrid: document.getElementById('nodes-grid'),
	form: document.getElementById('submit-form'),
	videoFile: document.getElementById('video-file'),
	opsJson: document.getElementById('ops-json'),
	submitBtn: document.getElementById('submit-btn'),
	submitResult: document.getElementById('submit-result'),
	jobsList: document.getElementById('jobs-list'),
	jobItemTemplate: document.getElementById('job-item-template')
  };

  var trackedJobs = [];

  function api(path, options) {
	options = options || {};
	return fetch(path, options).then(function (res) {
	  return res.text().then(function (text) {
		var data = null;
		try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
		if (!res.ok) {
		  var msg = (data && data.detail) ? data.detail : (typeof data === 'string' ? data : 'HTTP ' + res.status);
		  throw new Error(msg);
		}
		return data;
	  });
	});
  }

  function refreshNodes() {
	api('/nodes').then(function (data) {
	  els.nodesGrid.innerHTML = '';
	  var reachable = 0;
	  (data.nodes || []).forEach(function (n) {
		if (n.reachable) reachable++;
		var card = document.createElement('div');
		card.className = 'node-card ' + (n.reachable ? 'reachable' : 'unreachable');
		var html = '<div class="node-url">' + n.url + '</div>';
		if (n.reachable && n.info) {
		  html += '<div class="node-metric"><span>ID</span><span>' + n.info.nodeId + '</span></div>';
		  html += '<div class="node-metric"><span>Status</span><span>' + n.info.status + '</span></div>';
		  html += '<div class="node-metric"><span>CPU</span><span>' + Math.round(n.info.cpuUsage) + '%</span></div>';
		  html += '<div class="node-metric"><span>MEM</span><span>' + Math.round(n.info.memoryUsage) + '%</span></div>';
		  html += '<div class="node-metric"><span>Queue</span><span>' + n.info.queueSize + '</span></div>';
		  html += '<div class="node-metric"><span>Active</span><span>' + n.info.activeJobs + '</span></div>';
		} else {
		  html += '<div class="node-error">' + (n.error || 'unreachable') + '</div>';
		}
		card.innerHTML = html;
		els.nodesGrid.appendChild(card);
	  });
	  els.nodesSummary.textContent = reachable + '/' + (data.nodes || []).length + ' nodes reachable | next round-robin index: ' + data.next_index;
	}).catch(function (err) {
	  els.nodesSummary.textContent = 'Failed: ' + err.message;
	});
  }

  function renderJob(job) {
	var found = null;
	for (var i = 0; i < trackedJobs.length; i++) {
	  if (trackedJobs[i].id === job.id) { found = trackedJobs[i]; break; }
	}
	if (!found) return;
	var node = els.jobsList.querySelector('[data-job-id="' + job.id + '"]');
	if (!node) {
	  node = els.jobItemTemplate.content.firstElementChild.cloneNode(true);
	  node.dataset.jobId = job.id;
	  els.jobsList.appendChild(node);
	}
	node.querySelector('.job-node').textContent = found.node_url;
	node.querySelector('.job-id').textContent = job.id;
	node.querySelector('.job-status').textContent = job.status || '';
	node.querySelector('.job-status').className = 'job-status ' + (job.status || '');
	node.querySelector('.progress-fill').style.width = (job.progress || 0) + '%';
	node.querySelector('.job-step').textContent = job.current_step ? ('Step: ' + job.current_step + ' (' + (job.step_index || 0) + '/' + (job.total_steps || 0) + ')') : '';
	node.querySelector('.job-error').textContent = job.error || '';
	var dl = node.querySelector('.job-download');
	if (job.status === 'COMPLETED') {
	  dl.href = '/result/' + encodeURIComponent(found.node_url) + '/' + job.id;
	  dl.classList.remove('hidden');
	} else {
	  dl.classList.add('hidden');
	}
  }

  function pollAll() {
	trackedJobs.forEach(function (t) {
	  api('/job/' + encodeURIComponent(t.node_url) + '/' + t.id).then(function (job) {
		renderJob(job);
	  }).catch(function () {});
	});
  }

  els.form.addEventListener('submit', function (e) {
	e.preventDefault();
	els.submitBtn.disabled = true;
	els.submitResult.classList.add('hidden');
	els.submitResult.classList.remove('error');
	var file = els.videoFile.files[0];
	if (!file) { els.submitBtn.disabled = false; return; }
	var ops;
	try {
	  ops = JSON.parse(els.opsJson.value);
	  if (!Array.isArray(ops) || ops.length === 0) throw new Error('Operations must be a non-empty array');
	} catch (err) {
	  els.submitResult.textContent = 'Invalid operations JSON: ' + err.message;
	  els.submitResult.classList.add('error');
	  els.submitResult.classList.remove('hidden');
	  els.submitBtn.disabled = false;
	  return;
	}

	var fd = new FormData();
	fd.append('file', file);

	api('/submit-file', { method: 'POST', body: fd }).then(function (upload) {
	  var payload = { file_id: upload.id, operations: ops };
	  return api('/submit-job', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload)
	  }).then(function (job) {
		return { upload: upload, job: job };
	  });
	}).then(function (r) {
	  trackedJobs.push({ id: r.job.id, node_url: r.job.assigned_node });
	  els.submitResult.classList.remove('hidden');
	  els.submitResult.classList.remove('error');
	  els.submitResult.textContent = 'Job ' + r.job.id + ' assigned to ' + r.job.assigned_node;
	  renderJob(r.job);
	}).catch(function (err) {
	  els.submitResult.classList.remove('hidden');
	  els.submitResult.classList.add('error');
	  els.submitResult.textContent = 'Failed: ' + err.message;
	}).then(function () {
	  els.submitBtn.disabled = false;
	});
  });

  refreshNodes();
  setInterval(refreshNodes, 3000);
  setInterval(pollAll, 1500);
})();
