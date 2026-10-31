
const resumeFile = document.getElementById("resumeFile");

resumeFile.addEventListener("change", function () {
    const file = this.files[0];

    if (!file) return;

    const allowedExtensions = [".pdf", ".docx", ".txt"];

    const extension = file.name
        .substring(file.name.lastIndexOf("."))
        .toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        document.getElementById("status").textContent =
            "Please upload a PDF, DOCX or TXT file.";

        this.value = "";
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        document.getElementById("status").textContent =
            "File size must be less than 5 MB.";

        this.value = "";
        return;
    }

    document.getElementById("fileName").textContent =
        "Selected file: " + file.name;

    document.getElementById("status").textContent = "";
});


async function analyzeResume() {

    const resume = document.getElementById("resumeText").value.trim();

    const job = document.getElementById("jobText").value.trim();

    const file = resumeFile.files[0];

    const status = document.getElementById("status");

    const button = document.getElementById("analyzeBtn");

    status.textContent = "";

    if (!file && resume.length < 80) {

        status.textContent =
            "Please upload your resume or paste at least 80 characters.";

        return;
    }

    if (job.length < 40) {

        status.textContent =
            "Please enter at least 40 characters of job description.";

        return;
    }

    button.disabled = true;

    button.textContent = "Analyzing Resume...";

    document.getElementById("empty").classList.add("hidden");

    document.getElementById("results").classList.add("hidden");

    document.getElementById("loading").classList.remove("hidden");

    try {

        const formData = new FormData();

        if (file) {

            formData.append("resume_file", file);

        } else {

            formData.append("resume_text", resume);

        }

        formData.append("job_description", job);

        const response = await fetch("/api/analyze", {

            method: "POST",

            body: formData

        });

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail || "Resume analysis failed."
            );

        }

        document.getElementById("score").textContent =
            data.match_score + "%";

        document.getElementById("overview").textContent =
            data.ai_analysis;

        document.getElementById("summary").textContent =
            data.summary_suggestion;

        fillList("strengths", data.strengths);

        fillList("weaknesses", data.weaknesses);

        fillList("suggestions", data.suggestions);

        const skills = document.getElementById("skills");

        skills.replaceChildren();

        (data.recommended_skills || []).forEach(skill => {

            const tag = document.createElement("span");

            tag.className = "skill";

            tag.textContent = skill;

            skills.appendChild(tag);

        });

        document.getElementById("loading").classList.add("hidden");

        document.getElementById("results").classList.remove("hidden");

    } catch (error) {

        document.getElementById("loading").classList.add("hidden");

        document.getElementById("empty").classList.remove("hidden");

        status.textContent =
            error.message || "Unable to connect to the server.";

    } finally {

        button.disabled = false;

        button.textContent = "Analyze My Resume →";

    }
}


function fillList(id, items) {

    const list = document.getElementById(id);

    list.replaceChildren();

    (Array.isArray(items) ? items : []).forEach(item => {

        const li = document.createElement("li");

        li.textContent = String(item);

        list.appendChild(li);

    });

}
