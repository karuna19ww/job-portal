const jobList = document.getElementById("jobList");
const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");
const locationInput = document.getElementById("locationInput");
const typeInput = document.getElementById("typeInput");
const resultsLabel = document.getElementById("resultsLabel");
const jobCount = document.getElementById("jobCount");
const toast = document.getElementById("toast");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}
function escapeHTML(value = "") {
  return String(value).replace(/[&<>"']/g, char => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[char]));
}
function initials(company = "") {
  return company.trim().split(/\s+/).slice(0, 2).map(word => word[0] || "").join("").toUpperCase();
}
async function loadJobs() {
  jobList.innerHTML = '<div class="loading">Finding your next opportunity…</div>';
  const params = new URLSearchParams({
    search: searchInput.value.trim(),
    location: locationInput.value.trim(),
    type: typeInput.value
  });
  try {
    const response = await fetch(`/api/jobs?${params.toString()}`);
    if (!response.ok) throw new Error("Could not load jobs");
    const jobs = await response.json();
    resultsLabel.textContent = `${jobs.length} ${jobs.length === 1 ? "role" : "roles"} found`;
    jobCount.textContent = jobs.length;
    if (!jobs.length) {
      jobList.innerHTML = '<div class="empty-state">No matching jobs yet. Try a different keyword or clear your filters.</div>';
      return;
    }
    jobList.innerHTML = jobs.map(job => `
      <article class="job-card">
        <div class="job-card-top">
          <div class="company-mark">${escapeHTML(initials(job.company))}</div>
          <span class="job-type">${escapeHTML(job.job_type)}</span>
        </div>
        <h3>${escapeHTML(job.title)}</h3>
        <div class="company-name">${escapeHTML(job.company)}</div>
        <div class="job-meta"><span>⌖ ${escapeHTML(job.location)}</span></div>
        <p class="job-description">${escapeHTML(job.description)}</p>
        <div class="job-card-bottom">
          <span class="salary">${escapeHTML(job.salary)}</span>
          <button class="apply-button" data-apply="${job.id}" data-title="${escapeHTML(job.title)}">Apply now ↗</button>
        </div>
      </article>`).join("");
  } catch (error) {
    jobList.innerHTML = '<div class="empty-state">Could not connect to the backend. Check that the Flask server is running.</div>';
    resultsLabel.textContent = "Connection issue";
  }
}
searchForm.addEventListener("submit", event => { event.preventDefault(); loadJobs(); });
document.getElementById("clearFilters").addEventListener("click", () => {
  searchInput.value = ""; locationInput.value = ""; typeInput.value = "All types"; loadJobs();
});

function openModal(id) { document.getElementById(id).classList.remove("hidden"); }
function closeModal(id) { document.getElementById(id).classList.add("hidden"); }
document.getElementById("openPostTop").addEventListener("click", () => openModal("postModal"));
document.getElementById("openPostBottom").addEventListener("click", () => openModal("postModal"));
document.addEventListener("click", event => {
  const closeId = event.target.dataset.close;
  if (closeId) closeModal(closeId);
  const applyButton = event.target.closest("[data-apply]");
  if (applyButton) {
    document.getElementById("applyJobId").value = applyButton.dataset.apply;
    document.getElementById("applyJobName").textContent = applyButton.dataset.title;
    document.getElementById("applyMessage").textContent = "";
    openModal("applyModal");
  }
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape") document.querySelectorAll(".modal").forEach(modal => modal.classList.add("hidden"));
});

document.getElementById("applyForm").addEventListener("submit", async event => {
  event.preventDefault();
  const jobId = document.getElementById("applyJobId").value;
  const message = document.getElementById("applyMessage");
  const button = event.currentTarget.querySelector("button[type=submit]");
  button.disabled = true; button.textContent = "Submitting…";
  try {
    const response = await fetch(`/api/jobs/${jobId}/apply`, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        name: document.getElementById("applicantName").value,
        email: document.getElementById("applicantEmail").value,
        resume_link: document.getElementById("resumeLink").value,
        cover_letter: document.getElementById("coverLetter").value
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Application failed");
    message.textContent = result.message;
    event.currentTarget.reset();
    showToast("Application submitted!");
    setTimeout(() => closeModal("applyModal"), 1300);
  } catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; button.textContent = "Submit application"; }
});

document.getElementById("postForm").addEventListener("submit", async event => {
  event.preventDefault();
  const message = document.getElementById("postMessage");
  const button = event.currentTarget.querySelector("button[type=submit]");
  button.disabled = true; button.textContent = "Publishing…";
  try {
    const response = await fetch("/api/jobs", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        title: document.getElementById("postTitle").value,
        company: document.getElementById("postCompany").value,
        location: document.getElementById("postLocation").value,
        job_type: document.getElementById("postType").value,
        salary: document.getElementById("postSalary").value,
        description: document.getElementById("postDescription").value
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not publish job");
    message.textContent = "Job published successfully!";
    event.currentTarget.reset();
    await loadJobs();
    showToast("Your job is now listed.");
    setTimeout(() => closeModal("postModal"), 1000);
  } catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; button.textContent = "Publish job"; }
});

loadJobs();
