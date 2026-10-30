const resumeFile = document.getElementById("resumeFile");

resumeFile.addEventListener("change", async function () {
    const file = this.files[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".txt")) {
        document.getElementById("status").textContent =
            "Please upload a .txt file. You can paste PDF or DOCX text manually.";
        this.value = "";
        return;
    }

    if (file.size > 1000000) {
        document.getElementById("status").textContent =
            "Please choose a text file smaller than 1 MB.";
        this.value = "";
        return;
    }

    document.getElementById("resumeText").value = await file.text();
    document.getElementById("status").textContent = "";
});

async function analyzeResume() {
    const resume = document.getElementById("resumeText").value.trim();
    const job = document.getElementById("jobText").value.trim();
    const status = document.getElementById("status");
    const button = document.getElementById("analyzeBtn");

    status.textContent = "";

    if (resume.length < 80) {
        status.textContent = "Please enter at least 80 characters of resume text.";
        return;
    }

    if (job.length < 40) {
        status.textContent = "Please enter at least 40 characters of job description.";
        return;
    }

    button.disabled = true;
    button.textContent = "Analyzing...";
    document.getElementById("empty").classList.add("hidden");
    document.getElementById("results").classList.add("hidden");

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                resume_text: resume,
                job_description: job
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Analysis failed.");
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

        document.getElementById("results").classList.remove("hidden");

    } catch (error) {
        document.getElementById("empty").classList.remove("hidden");
        status.textContent = error.message ||
            "Unable to connect. Please check the server.";
    } finally {
        button.disabled = false;
        button.textContent = "Analyze My Resume";
    }
}

function fillList(id, items) {
    const list = document.getElementById(id);
    list.replaceChildren();

    (items || []).forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        list.appendChild(li);
    });
}
