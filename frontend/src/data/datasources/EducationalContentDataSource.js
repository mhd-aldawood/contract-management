import { getAccessToken } from '@/core/api/authSession'
// src/data/datasources/EducationalContentDataSource.js
import { API_URLS } from "@/core/config/apiUrls";
import { createLogger } from "@/core/logger";
import { apiRequest } from "@/core/api/apiClient";
const STORAGE_KEY = "app_educational_contents";
const log = createLogger("EducationalContentDataSource");

export default class EducationalContentDataSource {
  // ---------------- HTTP helper ----------------
  async _request(url, options = {}) {
    return apiRequest(url, options);
  }

  // ---------------- SAVE → POST /save ----------------
  async save(agreement) {
    const fileObject = agreement.file; // ← the File you just stored
    log.debug("save fileObject:", fileObject, fileObject instanceof File);

    const payload =
      typeof agreement?.toJSON === "function"
        ? agreement.toJSON()
        : { ...agreement };

    const fd = new FormData();

    for (const [key, value] of Object.entries(payload)) {
      if (key === "file" || key === "paymentSchedule" || key === "id") continue;
      if (value === null || value === undefined) continue;
      fd.append(key, key === "costTable" ? JSON.stringify(value) : typeof value === "boolean" ? String(value) : value);
    }

    if (Array.isArray(payload.paymentSchedule)) {
      fd.append("paymentSchedule", JSON.stringify(payload.paymentSchedule));
    }

    if (fileObject instanceof File || fileObject instanceof Blob) {
      fd.append("file", fileObject, fileObject.name);
      fd.append("fileName", fileObject.name);
    } else {
      log.debug("No File on agreement — upload will skip the file");
    }

    const token = getAccessToken();

    const saved = await this._request(API_URLS.educationalContents.create, {
      method: "POST",
      body: fd,
      headers: {
        ...(token ? { Authorization: `Token ${token}` } : {}),
      },
    });
    return saved;
  }

  async getAll() { return (await this._request(API_URLS.educationalContents.list)).data }
  async getByType() { return this.getAll() }
  async remove(id) { return this._request(API_URLS.educationalContents.byId(id), { method: 'DELETE' }) }
}
