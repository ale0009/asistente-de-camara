package com.example.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Database(
    entities = [Mission::class, ActionLogEntry::class, ObsidianNote::class],
    version = 1,
    exportSchema = false
)
abstract class NovaDatabase : RoomDatabase() {
    abstract fun missionDao(): MissionDao
    abstract fun actionLogDao(): ActionLogDao
    abstract fun obsidianNoteDao(): ObsidianNoteDao

    companion object {
        @Volatile
        private var INSTANCE: NovaDatabase? = null

        fun getDatabase(context: Context, scope: CoroutineScope): NovaDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    NovaDatabase::class.java,
                    "nova_database"
                )
                    .addCallback(NovaDatabaseCallback(scope))
                    .build()
                INSTANCE = instance
                instance
            }
        }

        private class NovaDatabaseCallback(
            private val scope: CoroutineScope
        ) : RoomDatabase.Callback() {
            override fun onCreate(db: SupportSQLiteDatabase) {
                super.onCreate(db)
                INSTANCE?.let { database ->
                    scope.launch(Dispatchers.IO) {
                        populateInitialData(
                            database.missionDao(),
                            database.actionLogDao(),
                            database.obsidianNoteDao()
                        )
                    }
                }
            }
        }

        private suspend fun populateInitialData(
            missionDao: MissionDao,
            logDao: ActionLogDao,
            obsidianDao: ObsidianNoteDao
        ) {
            // Seed initial missions matching design specs
            val defaultMissions = listOf(
                Mission(time = "06:00 AM", title = "Morning meditation & kata", isCompleted = true, category = "MINDFULNESS"),
                Mission(time = "07:30 AM", title = "Tactical Training Session", isCompleted = true, category = "TRAINING"),
                Mission(time = "10:00 AM", title = "Focus Sprint (90 min)", isCompleted = true, category = "DEEP_WORK"),
                Mission(time = "14:00 PM", title = "Skill Acquisition: Data Analysis", isCompleted = true, category = "STUDY"),
                Mission(time = "18:00 PM", title = "Evening Reflection & Log", isCompleted = true, category = "LOGGING")
            )
            missionDao.insertAll(defaultMissions)

            // Seed initial action logs
            logDao.insertLog(ActionLogEntry(timestamp = "06:01:45", source = "SYSTEM", message = "Focus Mode initialized.", logType = "INFO"))
            logDao.insertLog(ActionLogEntry(timestamp = "06:05:12", source = "CAMERA_1", message = "Motion detected.", logType = "INFO"))
            logDao.insertLog(ActionLogEntry(timestamp = "06:05:13", source = "AI_CORE", message = "Analyzing subject posture...", logType = "INFO"))
            logDao.insertLog(ActionLogEntry(timestamp = "06:07:30", source = "AI_CORE", message = "Flow State detected.", logType = "SUCCESS"))
            logDao.insertLog(ActionLogEntry(timestamp = "06:15:00", source = "COMMAND", message = "task_update --id=5 --status=complete", logType = "SUCCESS"))
            logDao.insertLog(ActionLogEntry(timestamp = "06:15:12", source = "SYSTEM", message = "All Daily Missions verified.", logType = "SUCCESS"))
            logDao.insertLog(ActionLogEntry(timestamp = "06:15:15", source = "SYNC", message = "Data uploaded successfully.", logType = "SUCCESS"))
            logDao.insertLog(ActionLogEntry(timestamp = "06:15:17", source = "NOVA", message = "ALL TASKS SYNCED", logType = "SUCCESS"))

            // Seed initial Obsidian notes
            obsidianDao.insertNote(
                ObsidianNote(
                    title = "Charter.md",
                    path = "D:\\Documentos\\Obsidian Vault\\NOVA\\Charter.md",
                    content = "# Charter del Proyecto NOVA\n\nVisión: Asistente local soberano 100% privado.\nGobernanza: NVIDIA RTX 5060 (8GB VRAM), keep_alive: 10m, think: false.\n\nESTADO: PROTEGIDO DE SOBREESCRITURA.",
                    isProtected = true
                )
            )
            obsidianDao.insertNote(
                ObsidianNote(
                    title = "OBSBOT_Tiny_3_Lite_Ficha_Tecnica.md",
                    path = "D:\\Documentos\\Obsidian Vault\\NOVA\\OBSBOT_Tiny_3_Lite_Ficha_Tecnica.md",
                    content = "# Ficha Técnica OBSBOT Tiny 3 Lite\n- Sensor: 1/2\" CMOS 48MP\n- Video: 4K@30fps HDR, 1080p@120fps\n- FOV: 79.1° (4:3) / 72° (16:9)\n- OSC Target: 127.0.0.1:16284\n- Pan Range: ±129° | Tilt Range: ±59°",
                    isProtected = false
                )
            )
            obsidianDao.insertNote(
                ObsidianNote(
                    title = "ADRs.md",
                    path = "D:\\Documentos\\Obsidian Vault\\NOVA\\ADRs.md",
                    content = "# Architectural Decision Records (ADRs)\n\nADR-001: Model Context Protocol (MCP) modular servers.\nADR-002: Whisper local STT + edge-tts.\nADR-003: DirectShow camera capture + pygrabber.",
                    isProtected = true
                )
            )
            obsidianDao.insertNote(
                ObsidianNote(
                    title = "reporte_addons.md",
                    path = "D:\\Documentos\\Obsidian Vault\\NOVA\\reporte_addons.md",
                    content = "# Reporte de Addons Blender & Herramientas\n- Blender 4.2 LTS Scripts\n- Integración OSC Bridge\n- Control por Voz de Vistas 3D",
                    isProtected = false
                )
            )
            obsidianDao.insertNote(
                ObsidianNote(
                    title = "Sesiones/2026-07-31.md",
                    path = "D:\\Documentos\\Obsidian Vault\\NOVA\\Sesiones\\2026-07-31.md",
                    content = "# Bitácora de Sesión - 31 de Julio de 2026\n- 06:00 AM - Inicio de Asistente NOVA\n- Modo Trabajo Activado\n- 5/5 Misiones Completadas\n- Tracking OSC Activo: Humano\n- Zoom: 1.0x",
                    isProtected = false
                )
            )
        }
    }
}
