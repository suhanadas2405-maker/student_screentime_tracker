let studentId = 1;

let availableApps = [];


// =====================================================
// LOAD ONLY THE 7 SUPPORTED APPS
// =====================================================

async function loadApps() {

    try {

        const response =
            await fetch("/api/apps");

        availableApps =
            await response.json();


        const container =
            document.getElementById(
                "appSelection"
            );

        container.innerHTML = "";


        availableApps.forEach(function(app) {

            const label =
                document.createElement("label");

            label.innerHTML = `
                <input
                    type="checkbox"
                    class="app-checkbox"
                    value="${app.app_name}"
                    data-package="${app.package_name}">

                <span>${app.app_name}</span>
            `;

            container.appendChild(label);

        });


        document
            .querySelectorAll(".app-checkbox")
            .forEach(function(box) {

                box.addEventListener(
                    "change",
                    updateLimitInputs
                );

            });


        updateUsageDropdown();

    }

    catch (error) {

        console.error(
            "Error loading apps:",
            error
        );

    }

}


// =====================================================
// DAILY LIMIT INPUTS
// =====================================================

function updateLimitInputs() {

    const container =
        document.getElementById(
            "limitSettings"
        );

    container.innerHTML = "";


    const selected =
        document.querySelectorAll(
            ".app-checkbox:checked"
        );


    if (selected.length === 0) {

        container.innerHTML =
            "<p>Select an app above.</p>";

        return;

    }


    selected.forEach(function(box) {

        const div =
            document.createElement("div");

        div.className =
            "limit-item";


        div.innerHTML = `

            <strong>
                ${box.value}
            </strong>

            <div>

                <input
                    type="number"
                    min="1"
                    value="30"
                    class="limit-input"
                    data-package="${box.dataset.package}">

                minutes/day

            </div>
        `;


        container.appendChild(div);

    });

}


// =====================================================
// USAGE DROPDOWN
// =====================================================

function updateUsageDropdown() {

    const dropdown =
        document.getElementById(
            "usageApp"
        );


    dropdown.innerHTML = `
        <option value="">
            Select App
        </option>
    `;


    availableApps.forEach(function(app) {

        const option =
            document.createElement("option");

        option.value =
            app.package_name;

        option.textContent =
            app.app_name;

        dropdown.appendChild(option);

    });

}


// =====================================================
// SAVE SETTINGS
// =====================================================

async function saveSettings() {

    const selected =
        document.querySelectorAll(
            ".app-checkbox:checked"
        );


    const message =
        document.getElementById(
            "saveMessage"
        );


    if (selected.length === 0) {

        message.textContent =
            "Please select at least one app.";

        return;

    }


    message.textContent =
        "Saving...";


    try {

        for (const box of selected) {

            await fetch(
                "/api/tracked-apps",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        student_id:
                            studentId,

                        app_name:
                            box.value,

                        package_name:
                            box.dataset.package

                    })
                }
            );


            const input =
                document.querySelector(
                    `.limit-input[data-package="${box.dataset.package}"]`
                );


            const limit =
                Number(input.value);


            await fetch(
                "/api/limits",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        student_id:
                            studentId,

                        package_name:
                            box.dataset.package,

                        daily_limit_minutes:
                            limit

                    })
                }
            );

        }


        message.textContent =
            "Settings saved successfully!";

        loadDashboard();

    }

    catch (error) {

        console.error(error);

        message.textContent =
            "Error saving settings.";

    }

}


// =====================================================
// RECORD USAGE
// =====================================================

async function recordUsage() {

    const packageName =
        document.getElementById(
            "usageApp"
        ).value;


    const minutes =
        Number(
            document.getElementById(
                "usageMinutes"
            ).value
        );


    const message =
        document.getElementById(
            "usageMessage"
        );


    if (!packageName || minutes < 0) {

        message.textContent =
            "Select an app and enter usage.";

        return;

    }


    try {

        const response =
            await fetch(
                "/api/usage",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        student_id:
                            studentId,

                        package_name:
                            packageName,

                        usage_minutes:
                            minutes

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            message.textContent =
                data.error;

            return;

        }


        if (data.warning) {

            alert(
                "⚠️ " + data.warning
            );

        }


        message.textContent =
            "Usage recorded successfully.";


        document.getElementById(
            "usageMinutes"
        ).value = "";


        loadDashboard();

    }

    catch (error) {

        console.error(error);

        message.textContent =
            "Could not record usage.";

    }

}


// =====================================================
// SUMMARY
// =====================================================

async function loadSummary() {

    const response =
        await fetch(
            `/api/summary/${studentId}`
        );


    const data =
        await response.json();


    document.getElementById(
        "totalUsage"
    ).textContent =
        `${data.total_usage_minutes} min`;


    document.getElementById(
        "appsTracked"
    ).textContent =
        data.apps_tracked;


    document.getElementById(
        "appsExceeded"
    ).textContent =
        data.apps_exceeded;

}


// =====================================================
// TODAY'S USAGE
// =====================================================

async function loadUsage() {

    const response =
        await fetch(
            `/api/usage/${studentId}`
        );


    const data =
        await response.json();


    const container =
        document.getElementById(
            "appUsage"
        );


    container.innerHTML = "";


    if (data.length === 0) {

        container.innerHTML =
            "<p>No usage recorded today.</p>";

        return;

    }


    data.forEach(function(app) {

        const card =
            document.createElement("div");


        card.className =
            "app-card";


        let status =
            "Normal";


        if (app.limit_exceeded) {

            status =
                "⚠️ Limit Exceeded";

        }

        else if (app.limit_reached) {

            status =
                "⚠️ Limit Reached";

        }

        else if (app.warning_sent) {

            status =
                "⚠️ Near Limit";

        }


        card.innerHTML = `

            <h3>
                ${app.app_name}
            </h3>

            <p>
                Usage:
                ${app.usage_minutes} minutes
            </p>

            <p>
                Limit:
                ${app.daily_limit_minutes ?? "-"}
                minutes
            </p>

            <strong>
                ${status}
            </strong>
        `;


        container.appendChild(card);

    });

}


// =====================================================
// HISTORY
// =====================================================

async function loadHistory() {

    const response =
        await fetch(
            `/api/history/${studentId}`
        );


    const data =
        await response.json();


    const table =
        document.getElementById(
            "historyTable"
        );


    table.innerHTML = "";


    data.forEach(function(record) {

        let status =
            "Normal";


        if (record.limit_exceeded) {

            status =
                "⚠️ Exceeded";

        }

        else if (record.limit_reached) {

            status =
                "⚠️ Reached";

        }

        else if (record.warning_sent) {

            status =
                "⚠️ Near Limit";

        }


        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                ${record.usage_date}
            </td>

            <td>
                ${record.app_name}
            </td>

            <td>
                ${record.usage_minutes} min
            </td>

            <td>
                ${record.daily_limit_minutes ?? "-"} min
            </td>

            <td>
                ${status}
            </td>
        `;


        table.appendChild(row);

    });

}


// =====================================================
// ADD STUDENT
// =====================================================

async function addStudent() {

    const name =
        document.getElementById(
            "studentName"
        ).value;


    const email =
        document.getElementById(
            "studentEmail"
        ).value;


    const message =
        document.getElementById(
            "studentMessage"
        );


    if (!name || !email) {

        message.textContent =
            "Enter student name and email.";

        return;

    }


    try {

        const response =
            await fetch(
                "/api/students",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        name: name,

                        email: email

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            message.textContent =
                data.error;

            return;

        }


        studentId =
            data.student_id;


        message.textContent =
            "Student added successfully.";


        loadDashboard();

    }

    catch (error) {

        console.error(error);

    }

}


// =====================================================
// DASHBOARD
// =====================================================

async function loadDashboard() {

    await loadSummary();

    await loadUsage();

    await loadHistory();

}


// =====================================================
// BUTTON EVENTS
// =====================================================

document
    .getElementById("saveSettings")
    .addEventListener(
        "click",
        saveSettings
    );


document
    .getElementById("recordUsage")
    .addEventListener(
        "click",
        recordUsage
    );


document
    .getElementById("addStudentButton")
    .addEventListener(
        "click",
        addStudent
    );


// =====================================================
// START
// =====================================================

loadApps();

loadDashboard();