(function () {
  'use strict';

  var state = {
	currentProject: null,
	currentFile: null,
	operations: [],
	pollTimer: null,
	pollJobId: null
  };

  var els = {
	nodeInfo: document.getElementById('node-info'),
	createProjectForm: document.getElementById('create-project-form'),
	projectName: document.getElementById('project-name'),
	projectList: document.getElementById('project-list'),
	projectView: document.getElementById('project-view'),
	currentProjectName: document.getElementById('current-project-name'),
	uploadForm: document.getElementById('upload-form'),
	videoFile: document.getElementById('video-file'),
	videoPreview: document.getElementById('video-preview'),
	fileMeta: document.getElementById('file-meta'),
	operationsSection: document.getElementById('operations-section'),
	operationsList: document.getElementById('operations-list'),
	opSelect: document.getElementById('op-select'),
	addOpBtn: document.getElementById('add-op-btn'),
	submitJobBtn: document.getElementById('submit-job-btn'),
	jobsSection: document.getElementById('jobs-section'),
	jobList: document.getElementById('job-list'),
	jobItemTemplate: document.getElementById('job-item-template')
  };

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

  function show(el) { el.classList.remove('hidden'); }
  function hide(el) { el.classList.add('hidden'); }

  function refreshNodeInfo() {
	api('/node/info').then(function (info) {
	  els.nodeInfo.textContent = 'Node ' + info.nodeId + ' | ' + info.status +
		' | CPU ' + Math.round(info.cpuUsage) + '%' +
		' | MEM ' + Math.round(info.memoryUsage) + '%' +
		' | Queue ' + info.queueSize +
		' | Active ' + info.activeJobs;
	}).catch(function (err) {
	  els.nodeInfo.textContent = 'Node info unavailable: ' + err.message;
	});
  }

  function loadProjects() {
	api('/projects').then(function (projects) {
	  els.projectList.innerHTML = '';
	  (projects || []).forEach(function (p) {
		var li = document.createElement('li');
		li.textContent = p.name;
		li.dataset.projectId = p.id;
		li.addEventListener('click', function () { openProject(p); });
		els.projectList.appendChild(li);
	  });
	}).catch(function (err) {
	  console.error('Failed to load projects', err);
	});
  }

  function openProject(project) {
	state.currentProject = project;
	state.currentFile = null;
	state.operations = [];
	els.currentProjectName.textContent = project.name;
	show(els.projectView);
	hide(els.videoPreview);
	hide(els.fileMeta);
	hide(els.operationsSection);
	renderOperations();
	loadProjectJobs(project.id);
	Array.prototype.forEach.call(els.projectList.children, function (li) {
	  li.classList.toggle('active', li.dataset.projectId === project.id);
	});
  }

  function loadProjectJobs(projectId) {
	api('/jobs?project_id=' + encodeURIComponent(projectId)).then(function (jobs) {
	  show(els.jobsSection);
	  els.jobList.innerHTML = '';
	  (jobs || []).forEach(function (job) {
		renderJob(job);
	  });
	}).catch(function (err) {
	  console.error('Failed to load jobs', err);
	});
  }

  function renderJob(job) {
	var existing = els.jobList.querySelector('[data-job-id="' + job.id + '"]');
	var node = existing || els.jobItemTemplate.content.firstElementChild.cloneNode(true);
	node.dataset.jobId = job.id;
	node.querySelector('.job-id').textContent = 'Job ' + job.id;
	node.querySelector('.job-status').textContent = job.status || '';
	node.querySelector('.job-status').className = 'job-status ' + (job.status || '');
	var fill = node.querySelector('.progress-fill');
	fill.style.width = (job.progress || 0) + '%';
	var step = node.querySelector('.job-step');
	if (job.current_step) {
	  step.textContent = 'Step: ' + job.current_step + ' (' + (job.step_index || 0) + '/' + (job.total_steps || 0) + ')';
	} else {
	  step.textContent = '';
	}
	var errEl = node.querySelector('.job-error');
	errEl.textContent = job.error || '';
	var dl = node.querySelector('.job-download');
	if (job.status === 'COMPLETED') {
	  dl.href = '/results/' + job.id;
	  show(dl);
	} else {
	  hide(dl);
	}
	if (!existing) {
	  els.jobList.appendChild(node);
	}
  }

  function pollJob(jobId) {
	if (state.pollTimer) clearInterval(state.pollTimer);
	state.pollJobId = jobId;
	state.pollTimer = setInterval(function () {
	  api('/jobs/' + jobId).then(function (job) {
		renderJob(job);
		if (job.status === 'COMPLETED' || job.status === 'FAILED') {
		  clearInterval(state.pollTimer);
		  state.pollTimer = null;
		  state.pollJobId = null;
		  els.submitJobBtn.disabled = false;
		}
	  }).catch(function (err) {
		console.error('Poll failed', err);
	  });
	}, 1500);
  }

  function renderOperations() {
	els.operationsList.innerHTML = '';
	state.operations.forEach(function (op, idx) {
	  var tpl = document.getElementById('op-' + op.op + '-template');
	  if (!tpl) return;
	  var node = tpl.content.firstElementChild.cloneNode(true);
	  node.dataset.index = idx;
	  Array.prototype.forEach.call(node.querySelectorAll('[data-field]'), function (input) {
		var field = input.dataset.field;
		if (op[field] !== undefined) input.value = op[field];
		input.addEventListener('input', function () {
		  var v = input.value;
		  op[field] = (input.type === 'number') ? (v === '' ? '' : Number(v)) : v;
		});
	  });
	  node.querySelector('.remove-op').addEventListener('click', function () {
		state.operations.splice(idx, 1);
		renderOperations();
	  });
	  els.operationsList.appendChild(node);
	});
  }

  function addOperation() {
	var op = els.opSelect.value;
	var defaults = {
	  trim: { op: 'trim', start: 0, end: 1 },
	  resize: { op: 'resize', width: 1280, height: 720 },
	  compress: { op: 'compress', crf: 23, preset: 'medium' },
	  convert: { op: 'convert', format: 'mp4' }
	};
	state.operations.push(defaults[op]);
	renderOperations();
  }

  els.createProjectForm.addEventListener('submit', function (e) {
	e.preventDefault();
	var name = els.projectName.value.trim();
	if (!name) return;
	api('/projects', {
	  method: 'POST',
	  headers: { 'Content-Type': 'application/json' },
	  body: JSON.stringify({ name: name })
	}).then(function (project) {
	  els.projectName.value = '';
	  loadProjects();
	  openProject(project);
	}).catch(function (err) {
	  alert('Create project failed: ' + err.message);
	});
  });

  els.uploadForm.addEventListener('submit', function (e) {
	e.preventDefault();
	if (!state.currentProject) return;
	var file = els.videoFile.files[0];
	if (!file) return;
	var fd = new FormData();
	fd.append('file', file);
	fd.append('project_id', state.currentProject.id);
	els.uploadForm.querySelector('button').disabled = true;
	api('/files', { method: 'POST', body: fd }).then(function (meta) {
	  state.currentFile = meta;
	  els.fileMeta.textContent = 'File ' + meta.id + ' | ' + (meta.duration ? meta.duration.toFixed(2) + 's' : '') + ' | ' + (meta.format || '');
	  show(els.fileMeta);
	  els.videoPreview.src = '/files/' + meta.id + '/content';
	  show(els.videoPreview);
	  show(els.operationsSection);
	}).catch(function (err) {
	  alert('Upload failed: ' + err.message);
	}).then(function () {
	  els.uploadForm.querySelector('button').disabled = false;
	});
  });

  els.addOpBtn.addEventListener('click', addOperation);

  els.submitJobBtn.addEventListener('click', function () {
	if (!state.currentProject || !state.currentFile) {
	  alert('Upload a file first.');
	  return;
	}
	if (state.operations.length === 0) {
	  alert('Add at least one operation.');
	  return;
	}
	var payload = {
	  file_id: state.currentFile.id,
	  project_id: state.currentProject.id,
	  operations: state.operations
	};
	els.submitJobBtn.disabled = true;
	api('/jobs', {
	  method: 'POST',
	  headers: { 'Content-Type': 'application/json' },
	  body: JSON.stringify(payload)
	}).then(function (job) {
	  renderJob(job);
	  pollJob(job.id);
	}).catch(function (err) {
	  alert('Submit job failed: ' + err.message);
	  els.submitJobBtn.disabled = false;
	});
  });

  refreshNodeInfo();
  setInterval(refreshNodeInfo, 5000);
  loadProjects();
})();
