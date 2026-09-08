package com.silveryarn.mobile.sync

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/** design.md §4.1 표준 응답 포맷 — apps/web·apps/admin의 lib/api/client.ts ApiEnvelope와
 * 동일 개념. Moshi는 전역 snake_case→camelCase 변환기가 없어(TS의 case.ts처럼 재귀
 * 변환 유틸 대신) 필드마다 @Json(name=)을 명시한다 — Kotlin/Retrofit 생태계의
 * 관용적 방식이라 굳이 커스텀 어댑터를 만들지 않았다. */
@JsonClass(generateAdapter = true)
data class ApiEnvelope<T>(
    val data: T? = null,
    val pagination: Pagination? = null,
    val error: ApiErrorBody? = null,
)

@JsonClass(generateAdapter = true)
data class Pagination(
    val page: Int,
    @Json(name = "page_size") val pageSize: Int,
    val total: Int,
)

@JsonClass(generateAdapter = true)
data class ApiErrorBody(
    val code: String,
    val message: String,
)

class ApiException(val code: String, message: String) : Exception(message)
