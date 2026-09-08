package com.silveryarn.mobile.local.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase

/**
 * mobile-schema.md 6개 테이블 중 5개는 Room `@Entity`로, `autobiography_fts`는
 * FTS5라 [Callback.onCreate]에서 raw SQL로 만든다(AutobiographyFts.kt 파일
 * 상단 주석 참조) — Room의 스키마 익스포트/검증 대상에는 안 잡히지만, 앱이
 * DB를 처음 여는 시점에 항상 같이 생성되므로 실사용에는 문제 없다.
 */
@Database(
    entities = [
        ConversationEntity::class,
        QuestionCacheEntity::class,
        UnrecalledPhotoEntity::class,
        ScheduleCacheEntity::class,
        DeviceStateEntity::class,
    ],
    version = 1,
    // 마이그레이션을 아직 안 쓰는 version=1 단계라 false — 스키마 export 디렉터리를
    // ksp room.schemaLocation 인자로 설정하지 않은 상태에서 true로 두면 빌드 경고만
    // 나온다. 실제 마이그레이션이 생기면 true로 바꾸고 디렉터리 설정 추가.
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun conversationDao(): ConversationDao
    abstract fun questionCacheDao(): QuestionCacheDao
    abstract fun unrecalledPhotoDao(): UnrecalledPhotoDao
    abstract fun scheduleCacheDao(): ScheduleCacheDao
    abstract fun deviceStateDao(): DeviceStateDao

    /** autobiography_fts는 Room `@Entity`가 아니라 raw SQL 테이블이라(AutobiographyFtsStore.kt
     * 주석 참조) `abstract fun`이 아니라 매번 새로 만드는 일반 함수다 — Room이 생성하는
     * DAO 구현체가 아니라 이 클래스가 직접 SupportSQLiteDatabase를 넘겨준다. */
    fun autobiographyFtsStore(): AutobiographyFtsStore = AutobiographyFtsStore(openHelper.writableDatabase)

    companion object {
        private const val DB_NAME = "silveryarn.db"

        @Volatile private var instance: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(context.applicationContext, AppDatabase::class.java, DB_NAME)
                    .addCallback(
                        object : Callback() {
                            override fun onCreate(db: SupportSQLiteDatabase) {
                                super.onCreate(db)
                                db.execSQL(CREATE_AUTOBIOGRAPHY_FTS_SQL)
                            }
                        },
                    )
                    .build()
                    .also { instance = it }
            }
    }
}
