import { createLogger } from "@/core/logger";
import { API_URLS } from "@/core/config/apiUrls";
import {apiRequest} from "@/core/api/apiClient.js";
const logger = createLogger("OtherAgreementRemoteDataSource");

export default class OtherAgreementRemoteDataSource {

    async save(form) {
        logger.debug("OtherAgreementLocalDataSource save", form);
        const tempPayload = form;
        logger.debug(tempPayload);

        const fileObject = tempPayload.file; // ← the File you just stored
        console.log("save fileObject:", fileObject, fileObject instanceof File);

        const payload =
            typeof tempPayload?.toJSON === "function"
                ? tempPayload.toJSON()
                : { ...tempPayload };

        const fd = new FormData();

        for (const [key, value] of Object.entries(payload)) {
            if (key === "file" ||key === "id"   || key === "rows" || key === "fileName"  ) continue;
            if (value === null || value === undefined) continue;
            fd.append(key, typeof value === "boolean" ? String(value) : value);
        }


        if (fileObject instanceof File || fileObject instanceof Blob) {
            fd.append("fileName", fileObject.name);
            fd.append("file", fileObject, fileObject.name);
        } else {
            console.warn("No File on agreement — upload will skip the file");
        }

        fd.append("rows", JSON.stringify(form.rows ?? []))

        const token = localStorage.getItem("access_token");

        const saved = await this._request(form.type === 'memorandum' ? API_URLS.memorandum.create : API_URLS.otherAgreement.create, {
            method: "POST",
            body: fd,
            headers: {
                ...(token ? { Authorization: `Token ${token}` } : {}),
            },
        });
        return saved;
    }

    async _request(url, options = {}) {
          return apiRequest(url, options);
    }

}
