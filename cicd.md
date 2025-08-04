# **CI/CD Pipeline Guide (GitLab CI + Terraform IaC)**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-04  
**Author**: addhe warman  

---

## **1. Overview**

Panduan ini menjelaskan proses CI/CD untuk:  
* **Infrastructure as Code (IaC)** menggunakan Terraform untuk provisioning resource GCP.  
* **Continuous Integration (CI)** untuk build & test kode Python Cloud Function.  
* **Continuous Deployment (CD)** otomatis ke GCP setelah merge ke branch utama.  

---

## **2. Goals**

* Deployment **otomatis** dan **reproducible**.  
* Kontrol penuh atas resource melalui Terraform.  
* Integrasi penuh dengan GitLab (pipeline, artifacts, secrets).  
* Mengurangi human error saat provisioning dan deployment.  

---

## **3. Architecture Overview**

```
[GitLab Repo] ----> [GitLab CI/CD Pipeline] ----> [Terraform Apply] ----> [GCP Resources]  
            \----> [Build & Deploy Cloud Function] ----------------------> [Gmail + Pub/Sub + Vertex AI]  
```

---

## **4. Requirements**

### **4.1 Tools**

* Terraform v1.5+  
* GitLab CI/CD Runners  
* gcloud CLI (di runner untuk validasi opsional)  

### **4.2 GitLab Variables**

Set di **GitLab → Settings → CI/CD → Variables**:  
* `GCP_PROJECT_ID`  
* `GCP_REGION` (contoh: `us-central1`)  
* `GCP_SERVICE_ACCOUNT_KEY` (JSON)  
* `TF_STATE_BUCKET` (bucket untuk remote backend Terraform)  

---

## **5. Repository Structure**

```
auto-reply-ai/  
├── cloud_function/  
│   ├── main.py  
│   ├── requirements.txt  
├── terraform/  
│   ├── main.tf  
│   ├── variables.tf  
│   ├── outputs.tf  
│   └── provider.tf  
├── .gitlab-ci.yml  
└── README.md  
```

---

## **6. Terraform Configuration**

### **6.1 provider.tf**

```hcl
terraform {  
  backend "gcs" {  
    bucket  = var.tf_state_bucket  
    prefix  = "auto-reply-ai/state"  
  }  
}  

provider "google" {  
  project = var.project_id  
  region  = var.region  
}  
```

### **6.2 main.tf**

* Buat resource Pub/Sub, Service Account, IAM binding, dan Cloud Function:  

```hcl
resource "google_pubsub_topic" "email_topic" {  
  name = "new-email"  
}  

resource "google_service_account" "autoreply_sa" {  
  account_id   = "autoreply-sa"  
  display_name = "Auto Reply Service Account"  
}  

resource "google_project_iam_binding" "sa_pubsub_subscriber" {  
  role    = "roles/pubsub.subscriber"  
  members = ["serviceAccount:${google_service_account.autoreply_sa.email}"]  
}  

resource "google_cloudfunctions_function" "auto_reply" {  
  name        = "auto-reply-email"  
  runtime     = "python311"  
  region      = var.region  
  entry_point = "pubsub_trigger"  
  source_archive_bucket = google_storage_bucket.function_source.name  
  source_archive_object = google_storage_bucket_object.source_code.name  
  event_trigger {  
    event_type = "google.pubsub.topic.publish"  
    resource   = google_pubsub_topic.email_topic.name  
  }  
}  
```

---

## **7. GitLab CI/CD Pipeline (.gitlab-ci.yml)**

### **7.1 Stages**

* **validate**: lint & validate Terraform + Python  
* **plan**: jalankan `terraform plan`  
* **apply**: jalankan `terraform apply` (deploy infra)  
* **deploy-function**: deploy kode Cloud Function  

---

### **7.2 Pipeline Config**

```yaml
stages:  
  - validate  
  - plan  
  - apply  
  - deploy-function  

variables:  
  TF_ROOT: "terraform"  
  CLOUD_FUNCTION_PATH: "cloud_function"  
  GOOGLE_APPLICATION_CREDENTIALS: "/tmp/key.json"  

before_script:  
  - echo "$GCP_SERVICE_ACCOUNT_KEY" > $GOOGLE_APPLICATION_CREDENTIALS  
  - gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS  
  - gcloud config set project $GCP_PROJECT_ID  

validate:  
  stage: validate  
  image: hashicorp/terraform:1.5  
  script:  
    - cd $TF_ROOT  
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"  
    - terraform validate  
    - pip install -r ../$CLOUD_FUNCTION_PATH/requirements.txt  
    - python -m py_compile ../$CLOUD_FUNCTION_PATH/main.py  

plan:  
  stage: plan  
  image: hashicorp/terraform:1.5  
  script:  
    - cd $TF_ROOT  
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"  
    - terraform plan -out=tfplan  
  artifacts:  
    paths:  
      - $TF_ROOT/tfplan  

apply:  
  stage: apply  
  image: hashicorp/terraform:1.5  
  script:  
    - cd $TF_ROOT  
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"  
    - terraform apply -auto-approve tfplan  
  when: manual  
  only:  
    - main  

deploy-function:  
  stage: deploy-function  
  image: google/cloud-sdk:slim  
  script:  
    - cd $CLOUD_FUNCTION_PATH  
    - zip -r function.zip *  
    - gsutil mb -p $GCP_PROJECT_ID gs://$CI_PROJECT_NAME-functions || true  
    - gsutil cp function.zip gs://$CI_PROJECT_NAME-functions/function.zip  
    - gcloud functions deploy auto-reply-email \  
        --runtime python311 \  
        --trigger-topic new-email \  
        --entry-point pubsub_trigger \  
        --region $GCP_REGION \  
        --source gs://$CI_PROJECT_NAME-functions/function.zip \  
        --service-account autoreply-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com \  
        --memory 256MB --timeout 60s  
  only:  
    - main  
```

---

## **8. Deployment Flow**

1. **Developer Commit** → push ke branch feature  
2. **Merge Request** → pipeline `validate` & `plan` otomatis jalan  
3. **Approval Merge ke main** → pipeline `apply` jalan manual (provision infra)  
4. **Deploy Function** → otomatis setelah apply sukses  
5. **Verify** → test end-to-end via email sample  

---

## **9. Rollback Strategy**

* Rollback infra: `terraform apply` versi sebelumnya / `terraform destroy` parsial.  
* Rollback function: `gcloud functions versions describe` & `rollback`.  

---

## **10. Security Considerations**

* Jangan commit file JSON service account ke repo.  
* Gunakan GitLab CI **masked variables** untuk credentials.  
* Batasi role Service Account hanya untuk resource yang dibutuhkan.  

---

## **11. Future Improvements**

* Tambahkan **Terraform Cloud** untuk state management.  
* Tambahkan lint & security scan (TFSEC, Bandit).  
* Integrasi **manual approval stage** untuk production deploy.  
* Otomatisasi testing setelah deploy via post-deploy job.
